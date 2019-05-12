from package_process.package_process import PackageProcess
from lprpm_conf import cfg, clean_section, \
                   pkg_states, add_item_to_section, \
                   delete_ppa_if_empty, delete_team_if_empty, \
                   check_installed
from multiprocessing.dummy import Pool as ThreadPool
import logging


class UninstallationProcess(PackageProcess):
    def __init__(self, msg_signal=None, log_signal=None, *args):
        super(UninstallationProcess, self).__init__(msg_signal=msg_signal, log_signal=log_signal, *args)
        self._section = 'uninstalling'
        self._error_section = 'failed_uninstalling'
        self._path_name = 'name'
        self._thread_pool = ThreadPool(10)

    def prepare_action(self):
        clean_section(pkg_states['uninstalling'])
        if bool(pkg_states['uninstalling']):
            for team in pkg_states['uninstalling']:
                for ppa in pkg_states['uninstalling'][team]:
                    for pkg_id in pkg_states['uninstalling'][team][ppa]:
                        if not check_installed(pkg_states['uninstalling'][team][ppa][pkg_id]['name'],
                                               pkg_states['uninstalling'][team][ppa][pkg_id]['version']):
                            self._msg_signal.emit("there is an error in the cache. " +
                                                  pkg_states['uninstalling'][ppa][pkg_id]['name'] +
                                                  " is not installed.")
                            self._log_signal.emit("there is an error in the cache. " +
                                                  pkg_states['uninstalling'][ppa][pkg_id]['name'] +
                                                  " is not installed.  If the problem continues," +
                                                  "Find the cache section in the config file," +
                                                  " at USERHOME/.config/kxfed/kxfed.cfg" +
                                                  " and delete the package from the uninstalling section.",
                                                  logging.CRITICAL)
                            raise FileNotFoundError("Cache Error " + ppa + " " + pkg_id)
        cfg.write()
        return False

    def change_state(self):
        uninstall_msg_txt = ""
        if cfg['uninstall'] == 'True':
            clean_section(pkg_states[self._section])
            if pkg_states[self._section]:
                for team in pkg_states[self._section]:
                    for ppa in pkg_states[self._section][team]:
                        for pkg in pkg_states[self._section][team][ppa]:
                            uninstall_msg_txt += pkg_states[self._section][team][ppa][pkg]['name'] + "\n"
                    if uninstall_msg_txt:
                        uninstall_msg_txt = "This will uninstall: \n" + uninstall_msg_txt
        return uninstall_msg_txt

    @staticmethod
    def action_pkgs():
        pkg_links = []
        for team in pkg_states['uninstalling']:
            for ppa in pkg_states['uninstalling'][team]:
                for pkg in pkg_states['uninstalling'][ppa][team]:
                    pkg_links.append('uninstalling' + pkg_states['uninstalling'][team][ppa][pkg]['name'])
        return pkg_links

    def move_cache(self):
        """"""
        for team in pkg_states[self._section]:
            for ppa in pkg_states[self._section][team]:
                for pkg_id in pkg_states[self._section][team][ppa]:
                    if not check_installed(pkg_states[self._section][team][ppa][pkg_id]['name'],
                                           pkg_states[self._section][team][ppa][pkg_id]['version']):
                        pkg_states[self._section][team][ppa].pop(pkg_id)
                    else:
                        add_item_to_section(self._error_section, pkg_states[self._section][team][ppa][pkg_id])
                delete_ppa_if_empty(self._section, team, ppa)
                delete_team_if_empty(self._section, team)
        cfg.write()
