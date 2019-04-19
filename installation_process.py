from package_process import PackageProcess
from kfconf import cfg, clean_section, pkg_states, delete_ppa_if_empty, add_item_to_section
from os.path import isfile
from multiprocessing.dummy import Pool as ThreadPool


class InstallationProcess(PackageProcess):
    def __init__(self, *args):
        super(InstallationProcess, self).__init__(args)
        self._section = 'installing'
        self._thread_pool = ThreadPool(10)

    def prepare_action(self):
        clean_section(pkg_states['installing'])
        if bool(pkg_states['installing']):
            for ppa in pkg_states['installing']:
                for pkg_id in pkg_states['installing'][ppa]:
                    if isfile(pkg_states['installing'][ppa][pkg_id]['rpm_path']):
                        if self.check_installed(pkg_states['installing'][ppa][pkg_id]['name']):
                            try:
                                if not pkg_states['installed'][ppa][pkg_id]:
                                    add_item_to_section('installed', pkg_states['installing'][ppa].pop(pkg_id))
                            except KeyError:
                                pkg_states['installed'][ppa] = {}
                                pkg_states['installed'][ppa][pkg_id] = pkg_states['installing'][ppa].pop(pkg_id)
                    else:
                        add_item_to_section('failed_installation', pkg_states['installing'][ppa].pop(pkg_id))
        cfg.write()

    def state_change(self):
        if cfg['install'] == 'True' or cfg['uninstall'] == 'True':
            clean_section(pkg_states[self._section])
            if pkg_states[self._section]:
                install_msg_txt = ""
                for ppa in pkg_states[self._section]:
                    for pkg in pkg_states[self._section][ppa]:
                        if isfile(pkg_states[self._section][ppa][pkg]['rpm_path']):
                            install_msg_txt += pkg_states[self._section][ppa][pkg]['name'] + "\n"
                    delete_ppa_if_empty(self._section, ppa)
                if install_msg_txt:
                    install_msg_txt = "This will install: \n" + install_msg_txt
        return install_msg_txt

    @staticmethod
    def action_rpms():
        rpm_links = []
        for ppa in pkg_states['installing']:
            for pkg in pkg_states['installing'][ppa]:
                if isfile(pkg_states['installing'][ppa][pkg]['rpm_path']):
                    rpm_links.append(pkg_states['installing'][ppa][pkg]['rpm_path'])
        return rpm_links

    def _install_debs(self):
        pass

