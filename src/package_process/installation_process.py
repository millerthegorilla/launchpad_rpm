from package_process.package_process import PackageProcess
from lprpm_conf import cfg, clean_section, pkg_states, delete_ppa_if_empty, add_item_to_section, check_installed
from os.path import isfile
from multiprocessing.dummy import Pool as ThreadPool


class InstallationProcess(PackageProcess):
    def __init__(self, *args, msg_signal=None, log_signal=None):
        super(InstallationProcess, self).__init__(*args, msg_signal=msg_signal, log_signal=log_signal)
        self._section = 'installing'
        self._next_section = 'installed'
        self._error_section = 'failed_installing'
        self._path_name = 'name'
        self._path_type = ""
        self._thread_pool = ThreadPool(10)

    def change_state(self):
        install_msg_txt = ""
        if cfg['install'] == 'True':
            clean_section(pkg_states[self._section])
            if pkg_states[self._section]:
                for ppa in pkg_states[self._section]:
                    for pkg in pkg_states[self._section][ppa]:
                        if isfile(pkg_states[self._section][ppa][pkg][self._path_type]):
                            install_msg_txt += pkg_states[self._section][ppa][pkg][self._path_name] + "\n"
                    delete_ppa_if_empty(self._section, ppa)
                if install_msg_txt:
                    install_msg_txt = "This will install: \n" + install_msg_txt
        return install_msg_txt

    def action_pkgs(self):
        pkg_links = []
        for ppa in pkg_states['installing']:
            for pkg in pkg_states['installing'][ppa]:
                if isfile(pkg_states['installing'][ppa][pkg][self._path_type]):
                    pkg_links.append(pkg_states['installing'][ppa][pkg][self._path_type])
        return pkg_links

    def move_cache(self):
        """"""
        for ppa in pkg_states[self._section]:
            for pkg_id in pkg_states[self._section][ppa]:
                if check_installed(pkg_states[self._section][ppa][pkg_id]['name'],
                                   pkg_states[self._section][ppa][pkg_id]['version']):
                    add_item_to_section(self._next_section, pkg_states[self._section][ppa].pop(pkg_id))
                else:
                    add_item_to_section(self._error_section, pkg_states[self._section][ppa].pop(pkg_id))
            delete_ppa_if_empty(self._section, ppa)
        cfg.write()

    def _install_debs(self):
        pass


class RPMInstallationProcess(InstallationProcess):
    def __init__(self, *args, msg_signal=None, log_signal=None):
        super(RPMInstallationProcess, self).__init__(*args, msg_signal=msg_signal, log_signal=log_signal)
        self._path_type = "rpm_path"

    def change_state(self):
        return super().change_state()


class DEBInstallationProcess(InstallationProcess):
    def __init__(self, *args, msg_signal=None, log_signal=None):
        super(DEBInstallationProcess, self).__init__(*args, msg_signal=msg_signal, log_signal=log_signal)
        self._path_type = "deb_path"

    def change_state(self):
        return super().change_state()
