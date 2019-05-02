from package_process import PackageProcess
from installation_process import RPMInstallationProcess, DEBInstallationProcess
from uninstallation_process import UninstallationProcess
from kfconf import cfg, tmp_dir, has_pending, ENDED_ERR, SCRIPT_PATH
from subprocess import Popen, PIPE
from PyQt5.QtGui import QGuiApplication
import logging
from multiprocessing.dummy import Pool as ThreadPool


class ActionProcess(PackageProcess):

    def __init__(self, *args,
                 pkg_type=None,
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
        self._populate_pkgs_signal=populate_pkgs_signal
        self._action_timer_signal=action_timer_signal
        self._processes = []
        self._errors = 0
        self._action_finished_signal = None
        self._timer = None
        self._progress_bar_num = 0
        if pkg_type == 'rpm':
            self._script = "dnf_install.py"
        elif pkg_type == 'deb':
            self._script = "deb_install.py"
        if cfg.as_bool('install'):
            if has_pending('installing'):
                if pkg_type == 'rpm':
                    self._installation_process = RPMInstallationProcess(msg_signal=msg_signal, log_signal=log_signal)
                    self._processes.append(self._installation_process)
                elif pkg_type == 'deb':
                    self._installation_process = DEBInstallationProcess(msg_signal=msg_signal, log_signal=log_signal)
                    self._processes.append(self._installation_process)

        if cfg.as_bool('uninstall'):
            if has_pending('uninstalling'):
                self._uninstallation_process = UninstallationProcess(msg_signal=msg_signal, log_signal=log_signal)
                self._processes.append(self._uninstallation_process)

    def prepare_action(self):
        moved = False
        for process in self._processes:
            moved = process.prepare_action() | moved
        return moved

    def read_section(self):
        for process in self._processes:
            process.read_section()

    def state_change(self, action_finished_signal):
        self._action_finished_signal = action_finished_signal
        self._errors = 0
        self._log_signal.emit("Actioning packages...", logging.INFO)
        self._msg_signal.emit("Actioning packages...")
        msg_txt = ""
        for process in self._processes:
            msg_txt = process.state_change()
        self._request_action_signal.emit(msg_txt, self.continue_actioning_if_ok)
        if self._errors:
            return 0, len(self) - self._errors
        else:
            return 1, len(self)

    def continue_actioning_if_ok(self):
        if cfg['distro_type'] == 'rpm':
            pkg_links = []
            for process in self._processes:
                pkg_links = pkg_links + process.action_rpms()
            self._thread_pool.apply_async(self._action_rpms, (pkg_links,), callback=self._finish_actioning)
        else:
            self._install_debs()

    def _finish_actioning(self, num_of_action):
        if num_of_action == 0:
            if self._errors:
                self._ended_signal.emit(ENDED_ERR)
        self._action_finished_signal.emit((self._errors, num_of_action, self))

    def _action_rpms(self, pkg_links):
        try:
            if pkg_links:
                self.process = Popen(['pkexec',
                                     SCRIPT_PATH + self._script,
                                      tmp_dir] + pkg_links,
                                     stdin=PIPE,
                                     stdout=PIPE,
                                     stderr=PIPE)
            else:
                raise ValueError("Error! : rpm_paths of packages in cache may be empty")
        except Exception as e:
            self._log_signal.emit(e, logging.CRITICAL)

        while 1:
            QGuiApplication.instance().processEvents()
            line = self.process.stdout.readline().decode('utf-8')
            self.process.stdout.flush()
            if line:
                # self.log_signal.emit(line, logging.INFO)
                if 'kxfedlog' in line:
                    self._log_signal.emit(line.lstrip('kxfedlog'), logging.INFO)
                if 'kxfedexcept' in line:
                    self._log_signal.emit(line.lstrip('kxfedexcept'), logging.CRITICAL)
                    self._msg_signal.emit('Error Installing! Check messages...')
                    self._errors += 1
                if 'kxfedmsg' in line:
                    self._msg_signal.emit(line.lstrip('kxfedmsg'))
                if 'kxfedprogress' in line:
                    sig = line.split(' ')
                    self._progress_signal.emit(sig[1], sig[2])
                if 'kxfedtransprogress' in line:
                    sig = line.split(' ')
                    if sig[1] == sig[2]:
                        self._msg_signal.emit('Verifying package, please wait...')
                    self._transaction_progress_signal.emit(sig[1], sig[2])
                if 'kxfedinstalled' in line:
                    name = line.lstrip('kxfedinstalled').replace('\n', '').strip()
                    self._msg_signal.emit('Installed ' + name)
                    self._log_signal.emit('Installed ' + name, logging.INFO)
                    # section = pkg_search(['installing'], name)
                    # add_item_to_section('installed', pkg_states['installing'][section.parent.parent.items()[0][0]].pop(section['id']))
                    # TODO schedule check or callback to run rpm.db_match to check install ok
                if 'kxfeduninstalled' in line:
                    name = line.lstrip('kxfeduninstalled').replace('\n', '').strip()
                    self._msg_signal.emit('Uninstalled ' + line.lstrip('kxfeduninstalled'))
                    self._log_signal.emit('Uninstalled ' + line.lstrip('kxfeduninstalled'), logging.INFO)
                    # section = pkg_search(['uninstalling'], name)
                    # pkg_states['uninstalling'][section.parent.parent.items()[0][0]].pop(section['id'])
                if 'verif' in line:
                    self._msg_signal.emit(line)
                    self._log_signal.emit(line, logging.INFO)
                    self._action_timer_signal.emit(True)
                # TODO delete package from uninstalled state
                # TODO change highlighted color of checkbox row to normal color
                # TODO delete rpm if it says so in the preferences
                if 'kxfedstop' in line:
                    self._msg_signal.emit("Transaction ", line.lstrip('kxfedstop'), " has finished")
                    self._log_signal.emit("Transaction ", line.lstrip('kxfedstop'), " has finished", logging.INFO)
            else:
                if self.process.poll() is not None:
                    self._progress_signal.emit(0, 0)
                    self._transaction_progress_signal.emit(0, 0)
                    break
        return len(pkg_links) - self._errors

    def _install_debs(self):
        pass

    def move_cache(self):
        for process in self._processes:
            process.move_cache()

    def __len__(self):
        length = 0
        for a in self._processes:
            length += len(a)
        return length

