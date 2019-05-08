from abc import abstractmethod
from kfconf import cfg, pkg_states, debs_dir, rpms_dir, \
                    add_item_to_section, clean_section, \
                    delete_ppa_if_empty, check_installed
from os.path import isfile
from collections import namedtuple
from fuzzywuzzy import process, fuzz
import logging
from pathlib import Path
from threading import RLock


class PackageProcess(list):
    """An abstract base class that extends also from list. The abstract methods define an interface
        that must be implemented by the sub classes"""
    def __init__(self, *args, msg_signal=None, log_signal=None):
        super(PackageProcess, self).__init__(*args)
        self._section = ""
        self._error_section = ""
        self._next_section = ""
        self._path_name = ""
        self._pkg_tuple = namedtuple("pkg_tuple", ["ppa", "pkg"])
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self.action_finished_callback = None
        self._lock = RLock()
        self._transaction = [self.prepare_action,
                             self.read_section,
                             self.change_state]
        self._iter = iter(self._transaction)

    @property
    def section(self):
        return self._section

    def transaction_iter(self):
        return self._iter

    def prepare_action(self):
        moved_section = False
        clean_section(pkg_states[self._section])
        if bool(pkg_states[self._section]):
            for ppa in pkg_states[self._section]:
                for pkg_id in pkg_states[self._section][ppa]:
                    pkg = pkg_states[self._section][ppa][pkg_id]
                    if check_installed(pkg['name'], pkg['version']):
                        self._msg_signal.emit("Package " +
                                              pkg["name"] +
                                              " is already installed, moving to installed list")
                        self._log_signal.emit("Package " +
                                              pkg["name"] +
                                              " is already installed, moving to installed list",
                                              logging.INFO)
                        moved_section = add_item_to_section("installed", pkg_states[self._section][ppa].pop(pkg_id))
                        continue
                    if cfg['distro_type'] == "rpm":
                        if not isfile(pkg["rpm_path"]):
                            paths = list(Path(rpms_dir).glob(pkg["name"] + "*"))
                            if paths:
                                fp = process.extractOne(pkg['name'] + pkg["version"],
                                                        paths,
                                                        scorer=fuzz.token_sort_ratio)
                                if fp:
                                    if fuzz.token_set_ratio(fp[0], pkg['name'] + pkg['version']) > 70:
                                        self._msg_signal.emit("Package " +
                                                              pkg["name"] +
                                                              " has already been converted, moving to installation list")
                                        self._log_signal.emit("Package " +
                                                              pkg["name"] +
                                                              " has already been converted, moving to installation list",
                                                              logging.INFO)
                                        pkg["rpm_path"] = fp[0]
                        if isfile(pkg_states[self._section][ppa][pkg_id]["rpm_path"]):
                            if self._section != "installing":
                                moved_section = add_item_to_section("installing", pkg_states[self._section][ppa].pop(pkg_id))
                            cfg.write()
                            continue
                        if not isfile(pkg["deb_path"]):
                            paths = list(Path(debs_dir).glob(pkg["name"] + "*"))
                            if paths:
                                fp = process.extractOne(pkg['name'] + pkg["version"],
                                                        paths,
                                                        scorer=fuzz.token_sort_ratio)
                                if fp:
                                    if fuzz.token_set_ratio(fp[0], pkg['name'] + pkg['version']) > 70:
                                        self._msg_signal.emit("Package " +
                                                              pkg["name"] +
                                                              " has already been downloaded, moving to conversion list")
                                        self._log_signal.emit("Package " +
                                                              pkg["name"] +
                                                              " has already been downloaded, moving to conversion list",
                                                              logging.INFO)
                                        pkg["deb_path"] = fp[0]
                            if isfile(pkg_states[self._section][ppa][pkg_id]["deb_path"]):
                                if self._section != "converting":
                                    moved_section = add_item_to_section("converting",
                                                                pkg_states[self._section][ppa].pop(pkg_id))
                            else:
                                pkg_states[self._section][ppa][pkg_id]["deb_path"] = ""
                                if self._section != "downloading":
                                    moved_section = add_item_to_section("tobeinstalled",
                                                                pkg_states[self._section][ppa].pop(pkg_id))
                            cfg.write()
                            continue
                    elif cfg['distro_type'] == "deb":
                        if not isfile(pkg["deb_path"]):
                            paths = list(Path(debs_dir).glob(pkg["name"] + "*"))
                            if paths:
                                fp = process.extractOne(pkg['name'] + pkg["version"],
                                                        paths,
                                                        scorer=fuzz.token_sort_ratio)
                                if fp:
                                    if fuzz.token_set_ratio(fp[0], pkg['name'] + pkg['version']) > 70:
                                        self._msg_signal.emit("Package " +
                                                              pkg["name"] +
                                                              " has already been downloaded, moving to installation list")
                                        self._log_signal.emit("Package " +
                                                              pkg["name"] +
                                                              " has already been downloaded, moving to installation list",
                                                              logging.INFO)
                                        pkg["deb_path"] = fp[0]
                        if isfile(pkg_states[self._section][ppa][pkg_id]["deb_path"]):
                            if self._section != "installing":
                                moved_section = add_item_to_section("installing",
                                                            pkg_states[self._section][ppa].pop(pkg_id))
                        else:
                            pkg_states[self._section][ppa][pkg_id]["deb_path"] = ""
                            if self._section != 'downloading':
                                moved_section = add_item_to_section("tobeinstalled",
                                                            pkg_states[self._section][ppa].pop(pkg_id))
                        continue

        cfg.write()
        return moved_section

    def read_section(self):
        """Reads the section from the cache as a list of packages (self)."""
        for ppa in pkg_states[self._section]:
            for pkg_id in pkg_states[self._section][ppa]:
                self.append(self._pkg_tuple(ppa=ppa, pkg=pkg_states[self._section][ppa][pkg_id]))
        return len(self)

    @property
    def section(self):
        return self._section

    @abstractmethod
    def change_state(self):
        """Each process, download, convert, install, uninstall, must check if the package is installed
            before it continues"""
        pass

    def move_cache(self):
        """"""
        moved = False
        for ppa in pkg_states[self._section]:
            for pkg_id in pkg_states[self._section][ppa]:
                if isfile(pkg_states[self._section][ppa][pkg_id][self._path_name]):
                    moved = add_item_to_section(self._next_section, pkg_states[self._section][ppa].pop(pkg_id))
                else:
                    moved = add_item_to_section(self._error_section, pkg_states[self._section][ppa].pop(pkg_id))
            delete_ppa_if_empty(self._section, ppa)
        cfg.write()
        return moved

