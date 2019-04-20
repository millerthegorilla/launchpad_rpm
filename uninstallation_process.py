from package_process import PackageProcess
from kfconf import cfg, clean_section, pkg_states, add_item_to_section, delete_ppa_if_empty
from multiprocessing.dummy import Pool as ThreadPool
import logging


class UninstallationProcess(PackageProcess):
    def __init__(self, *args, msg_signal=None, log_signal=None):
        super(UninstallationProcess, self).__init__(args, msg_signal=msg_signal, log_signal=log_signal)
        self._section = 'uninstalling'
        self._error_section = 'failed_uninstalling'
        self._path_name = 'name'
        self._thread_pool = ThreadPool(10)

    def prepare_action(self):
        clean_section(pkg_states['uninstalling'])
        if bool(pkg_states['uninstalling']):
            for ppa in pkg_states['uninstalling']:
                for pkg_id in pkg_states['uninstalling'][ppa]:
                    if not self.check_installed(pkg_states['uninstalling'][ppa][pkg_id]['name']):
                        self._msg_signal.emit("there is an error in the cache. " +
                                              pkg_states['uninstalling'][ppa][pkg_id]['name'] +
                                              " is not installed.")
                        self._log_signal.emit("there is an error in the cache. " +
                                              pkg_states['uninstalling'][ppa][pkg_id]['name'] +
                                              " is not installed.  Find the cache section in the config file," +
                                              " at USERHOME/.config/kxfed/kxfed.cfg" +
                                              " and delete the package from the uninstalling section.",
                                              logging.CRITICAL)
        cfg.write()

    def state_change(self):
        uninstall_msg_txt = ""
        if cfg['uninstall'] == 'True':
            clean_section(pkg_states[self._section])
            if pkg_states[self._section]:
                for ppa in pkg_states[self._section]:
                    for pkg in pkg_states[self._section][ppa]:
                        uninstall_msg_txt += pkg_states[self._section][ppa][pkg]['name'] + "\n"
                if uninstall_msg_txt:
                    uninstall_msg_txt = "This will uninstall: \n" + uninstall_msg_txt
        return uninstall_msg_txt

    @staticmethod
    def action_rpms():
        rpm_links = []
        for ppa in pkg_states['uninstalling']:
            for pkg in pkg_states['uninstalling'][ppa]:
                rpm_links.append('uninstalling' + pkg_states['uninstalling'][ppa][pkg]['name'])
        return rpm_links

    def move_cache(self):
        """"""
        for ppa in pkg_states[self._section]:
            for pkg_id in pkg_states[self._section][ppa]:
                if not self.check_installed(pkg_states[self._section][ppa][pkg_id][self._path_name]):
                    pkg_states[self._section][ppa].pop(pkg_id)
                else:
                    add_item_to_section(self._error_section, pkg_states[self._section][ppa][pkg_id])
            delete_ppa_if_empty(self._section, ppa)
        cfg.write()

    def _install_debs(self):
        pass

