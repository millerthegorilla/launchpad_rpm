from package_process import PackageProcess
from kfconf import cfg, clean_section, pkg_states, add_item_to_section
from multiprocessing.dummy import Pool as ThreadPool
from rpm import TransactionSet


class UninstallationProcess(PackageProcess):
    def __init__(self, *args):
        super(UninstallationProcess, self).__init__(args)
        self._section = 'uninstalling'
        self._thread_pool = ThreadPool(10)

    def prepare_action(self):
        clean_section(pkg_states['uninstalling'])
        if bool(pkg_states['uninstalling']):
            for ppa in pkg_states['uninstalling']:
                for pkgid in pkg_states['uninstalling'][ppa]:
                    ts = TransactionSet()
                    if not len(ts.dbMatch('name', pkg_states['uninstalling'][ppa][pkgid]['name'])):
                        self.msg_signal.emit("there is an error in the cache. ",
                                             pkg_states['uninstalling'][ppa][pkgid]['name'],
                                             "is not installed.")
                        self.log_signal.emit("there is an error in the cache. ",
                                             pkg_states['uninstalling'][ppa][pkgid]['name'],
                                             "is not installed.  Find the cache section in the config file,"
                                             " at USERHOME/.config/kxfed/kxfed.cfg",
                                             " and delete the package from the uninstalling section.")
        cfg.write()

    def state_change(self):
        if cfg['install'] == 'True' or cfg['uninstall'] == 'True':
            clean_section(pkg_states[self._section])
            if pkg_states[self._section]:
                uninstall_msg_txt = ""
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

    def _install_debs(self):
        pass

