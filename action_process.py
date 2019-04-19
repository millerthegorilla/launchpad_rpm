from package_process import PackageProcess
from installation_process import InstallationProcess
from uninstallation_process import UninstallationProcess
from kfconf import cfg, tmp_dir, add_item_to_section, pkg_search
from subprocess import Popen, PIPE
from PyQt5.QtGui import QGuiApplication
import logging
from multiprocessing.dummy import Pool as ThreadPool


class ActionProcess(PackageProcess):
    def __init__(self, *args,
                 request_action_signal=None,
                 log_signal=None,
                 msg_signal=None,
                 progress_signal=None,
                 transaction_progress_signal=None):
        super(ActionProcess, self).__init__(args)
        self._thread_pool = ThreadPool(10)
        self._section = "actioning"
        self._request_action_signal = request_action_signal
        self._log_signal = log_signal
        self._msg_signal = msg_signal
        self._progress_signal = progress_signal
        self._transaction_progress_signal = transaction_progress_signal
        self._processes = []
        if cfg.as_bool('install'):
            self._installation_process = InstallationProcess()
            self._processes.append(self._installation_process)
        if cfg.as_bool('uninstall'):
            self._uninstallation_process = UninstallationProcess()
            self._processes.append(self._uninstallation_process)

    def prepare_action(self):
        for process in self._processes:
            process.prepare_action()

    def read_section(self):
        for process in self._processes:
            process.read_section()

    def state_change(self):
        self._log_signal.emit("Actioning packages...", logging.INFO)
        self._msg_signal.emit("Actioning packages...")
        msg_txt = ""
        for process in self._processes:
            msg_txt = process.state_change()
        self._request_action_signal.emit(msg_txt, self.continue_actioning_if_ok)
        return 0, 0

    def continue_actioning_if_ok(self):
        if cfg['distro_type'] == 'rpm':
            self._thread_pool.apply_async(self._action_rpms)
        else:
            self._install_debs()

    def _action_rpms(self):
        rpm_links = []
        for process in self._processes:
            rpm_links = rpm_links + process.action_rpms()
        try:
            if rpm_links:
                self.process = Popen(['pkexec',
                                     '/home/james/Src/kxfed/dnf_install.py',
                                      tmp_dir] + rpm_links,
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
                elif 'kxfedexcept' in line:
                    self._log_signal.emit(line.lstrip('kxfedexcept'), logging.CRITICAL)
                    self._msg_signal.emit('Error Installing! Check messages...')
                elif 'kxfedmsg' in line:
                    self._msg_signal.emit(line.lstrip('kxfedmsg'))
                elif 'kxfedprogress' in line:
                    sig = line.split(' ')
                    self._progress_signal.emit(sig[1], sig[2])
                elif 'kxfedtransprogress' in line:
                    sig = line.split(' ')
                    if sig[1] == sig[2]:
                        self._msg_signal.emit('Verifying package, please wait...')
                    self._transaction_progress_signal.emit(sig[1], sig[2])
                elif 'kxfedinstalled' in line:
                    name = line.lstrip('kxfedinstalled').replace('\n', '').strip()
                    self._msg_signal.emit('Installed ' + name)
                    self._log_signal.emit('Installed ' + name, logging.INFO)
                    section = pkg_search(['installing'], name)
                    section.parent.pop(section['name'])
                    add_item_to_section('installed', section)
                    # TODO schedule check or callback to run rpm.db_match to check install ok
                elif 'kxfeduninstalled' in line:
                    name = line.lstrip('kxfeduninstalled').replace('\n', '').strip()
                    self._msg_signal.emit('Uninstalled ' + line.lstrip('kxfeduninstalled'))
                    self._log_signal.emit('Uninstalled ' + line.lstrip('kxfeduninstalled'))
                    section = self.pkg_search(['uninstalling'], name)
                    section.parent.pop(section['name'])
                # TODO delete package from uninstalled state
                # TODO change highlighted color of checkbox row to normal color
                # TODO delete rpm if it says so in the preferences
                elif 'kxfedstop' in line:
                    self._msg_signal.emit("Transaction ", line.lstrip('kxfedstop'), " has finished")
                    self._log_signal.emit("Transaction ", line.lstrip('kxfedstop'), " has finished")

                if line == '' and self.process.poll() is not None:
                    break

    def move_cache(self):
        for process in self._processes:
            process.move_cache()

