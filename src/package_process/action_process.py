from lprpm_conf import cfg, rpms_dir, has_pending, initialize_search, pkg_search, ENDED_ERR, SCRIPT_PATH
from subprocess import Popen, PIPE
from PyQt5.QtGui import QGuiApplication
import time
import logging
from multiprocessing.dummy import Pool as ThreadPool
from package_process.package_process import PackageProcess
from package_process.uninstallation_process import UninstallationProcess
if cfg['distro_type'] == 'rpm':
    from src.package_process.installation_process import RPMInstallationProcess
elif cfg['distro_type'] == 'deb':
    from src.package_process.installation_process import DEBInstallationProcess


class ActionProcess(PackageProcess):

    def __init__(self, *args,
                 request_action_signal=None,
                 log_signal=None,
                 msg_signal=None,
                 progress_signal=None,
                 transaction_progress_signal=None,
                 ended_signal=None,
                 populate_pkgs_signal=None,
                 action_timer_signal=None):
        super(ActionProcess, self).__init__(args)
        self._thread_pool = ThreadPool(10)
        self._section = "actioning"
        self._request_action_signal = request_action_signal
        self._log_signal = log_signal
        self._msg_signal = msg_signal
        self._progress_signal = progress_signal
        self._transaction_progress_signal = transaction_progress_signal
        self._ended_signal = ended_signal
        self._populate_pkgs_signal = populate_pkgs_signal
        self._action_timer_signal = action_timer_signal
        self._processes = []
        self._process = None
        self._errors = 0
        self._timer = None
        self._installation_process = None
        self._uninstallation_process = None
        self._progress_bar_num = 0

    def prepare_processes(self):
        if cfg.as_bool('install'):
            if has_pending('installing'):
                if cfg['distro_type'] == 'rpm':
                    self._installation_process = RPMInstallationProcess(msg_signal=self._msg_signal,
                                                                        log_signal=self._log_signal)
                elif cfg['distro_type'] == 'deb':
                    self._installation_process = DEBInstallationProcess(msg_signal=self._msg_signal,
                                                                        log_signal=self._log_signal)
                self._processes.append(self._installation_process)
        if cfg.as_bool('uninstall'):
            if has_pending('uninstalling'):
                self._uninstallation_process = UninstallationProcess(msg_signal=self._msg_signal,
                                                                     log_signal=self._log_signal)
                self._processes.append(self._uninstallation_process)

    def prepare_action(self):
        self.prepare_processes()
        moved = False
        for process in self._processes:
            moved = process.prepare_action() | moved
        return moved

    def read_section(self):
        for process in self._processes:
            process.read_section()
        return len(self)

    def change_state(self):
        self._log_signal.emit("Actioning packages...", logging.INFO)
        self._msg_signal.emit("Actioning packages...")
        msg_txt = ""
        for process in self._processes:
            msg_txt += process.change_state()
        self._request_action_signal.emit(msg_txt, self.continue_actioning_if_ok)

    def continue_actioning_if_ok(self):
        pkg_links = []
        cfg.write()
        for process in self._processes:
            pkg_links = pkg_links + process.action_pkgs()
        self._thread_pool.apply_async(self._action_pkgs, (pkg_links,), callback=self._finish_actioning)

    def _finish_actioning(self, num_of_action):
        if num_of_action == 0:
            if self._errors:
                self._ended_signal.emit(ENDED_ERR)
        initialize_search()
        self.action_finished_callback(self._errors, num_of_action, self)

    def _action_pkgs(self, pkg_links):
        try:
            if pkg_links:
                if cfg['distro_type'] == 'rpm':
                    self._process = Popen(['/usr/bin/pkexec',    # TODO auto detect path to pkexec
                                          SCRIPT_PATH + 'dnf_install.py',
                                          rpms_dir] + pkg_links,
                                          universal_newlines=True,
                                          bufsize=1,
                                          stdin=PIPE,
                                          stdout=PIPE,
                                          stderr=PIPE)
                elif cfg['distro_type'] == 'deb':
                    self._process = Popen(['/usr/bin/pkexec',
                                          SCRIPT_PATH + 'apt_install.py',
                                          rpms_dir] + pkg_links,
                                          universal_newlines=True,
                                          bufsize=1,
                                          stdin=PIPE,
                                          stdout=PIPE,
                                          stderr=PIPE)
            else:
                raise ValueError("Error! : links to installable packages \
                                 in cache may be empty; action_process.py line 115")
        except Exception as e:
            self._log_signal.emit(e, logging.CRITICAL)
        #now = time.time()
        timer_running = False
        while 1:
            QGuiApplication.instance().processEvents()
            line = self._process.stdout.readline().rstrip('\n')
            self._process.stdout.flush()
            if line:
                # if timer_running is False and time.time() - now > 5:
                #     timer_running = True
                #     self._action_timer_signal.emit(True)
                # self.log_signal.emit(line, logging.INFO)
                if 'kxfedlog' in line:
                    self._lock.acquire()
                    self._log_signal.emit(line.lstrip('kxfedlog'), logging.INFO)
                    self._lock.release()
                if 'kxfedexcept' in line:
                    self._lock.acquire()
                    self._log_signal.emit(line.lstrip('kxfedexcept'), logging.CRITICAL)
                    self._msg_signal.emit('Error Installing! Check messages...')
                    self._lock.release()
                    self._errors += 1
                if 'kxfedmsg' in line:
                    self._lock.acquire()
                    self._msg_signal.emit(line.lstrip('kxfedmsg'))
                    self._lock.release()
                if 'kxfedprogress' in line:
                    sig = line.split(' ')
                    self._lock.acquire()
                    self._progress_signal.emit(sig[1], sig[2])
                    self._lock.release()
                if 'kxfedtransprogress' in line:
                    sig = line.split(' ')
                    if sig[1] == sig[2]:
                        self._lock.acquire()
                        self._msg_signal.emit('Verifying package, please wait...')
                        self._lock.release()
                    self._lock.acquire()
                    self._transaction_progress_signal.emit(sig[1], sig[2])
                    self._lock.release()
                if 'kxfedinstalled' in line:
                    name = line.lstrip('kxfedinstalled').replace('\n', '').strip()
                    self._lock.acquire()
                    self._msg_signal.emit('Installed ' + name)
                    self._log_signal.emit('Installed ' + name, logging.INFO)
                    self._lock.release()
                if 'kxfeduninstalled' in line:
                    name = line.lstrip('kxfeduninstalled').replace('\n', '').strip()
                    self._lock.acquire()
                    self._msg_signal.emit('Uninstalled ' + name)
                    self._log_signal.emit('Uninstalled ' + name, logging.INFO)
                    self._lock.release()
                if 'kxfedverify_begin' in line:
                    self._lock.acquire()
                    self._log_signal.emit(line, logging.INFO)
                    if timer_running is False:
                        timer_running = True
                        self._action_timer_signal.emit(True)
                    self._lock.release()
                if 'kxfedverify_end' in line:
                    self._lock.acquire()
                    self._log_signal.emit(line, logging.INFO)
                    self._action_timer_signal.emit(False)
                    timer_running = False
                    self._progress_signal.emit(0, 0)
                    self._transaction_progress_signal.emit(0, 0)
                    self._lock.release()
                    break
            else:
                if self._process.poll() is not None:
                    self._lock.acquire()
                    self._progress_signal.emit(0, 0)
                    self._transaction_progress_signal.emit(0, 0)
                    self._action_timer_signal.emit(False)
                    timer_running = False
                    self._lock.release()

                    break
        return len(pkg_links) - self._errors

    def move_cache(self):
        for process in self._processes:
            process.move_cache()

    def __len__(self):
        length = 0
        for a in self._processes:
            length += len(a)
        return length
