from abc import abstractmethod
import rpm
from kfconf import cfg, pkg_states, debs_dir, rpms_dir, \
                    add_item_to_section, clean_section, \
                    delete_ppa_if_empty
from os.path import isfile, basename
from collections import namedtuple
from fuzzywuzzy import fuzz
import logging
from pathlib import Path


class PackageProcess(list):
    """An abstract base class that extends also from list. The abstract methods define an interface
        that must be implemented by the sub classes"""
    def __init__(self, *args, msg_signal=None, log_signal=None):
        super(PackageProcess, self).__init__(args)
        if not self[0]:
            del(self[0])
        self._section = ""
        self._error_section = ""
        self._next_section = ""
        self._path_name = ""
        self._pkg_tuple = namedtuple("pkg_tuple", ["ppa", "pkg"])
        self._msg_signal = msg_signal
        self._log_signal = log_signal

    def prepare_action(self):
        clean_section(pkg_states[self._section])
        if bool(pkg_states[self._section]):
            for ppa in pkg_states[self._section]:
                for pkg_id in pkg_states[self._section][ppa]:
                    pkg = pkg_states[self._section][ppa][pkg_id]
                    if self.check_installed(pkg['name']):
                        self._msg_signal.emit("Package " +
                                              pkg["name"] +
                                              " is already installed, moving to installed list")
                        self._log_signal.emit("Package " +
                                              pkg["name"] +
                                              " is already installed, moving to installed list",
                                              logging.INFO)
                        add_item_to_section("installed", pkg_states[self._section][ppa].pop(pkg_id))
                        continue
                    if not isfile(pkg["rpms_path"]):
                        paths = list(Path(rpms_dir).glob(pkg["name"] + "*"))
                        if paths and fuzz.token_set_ratio(pkg["version"],
                                                          basename(str(paths[0]).
                                                                           replace(pkg["name"] + "_", "")).
                                                                  rsplit("_", 1)[0]) > 90:
                            self._msg_signal.emit("Package " +
                                                  pkg["name"] +
                                                  " has already been converted, moving to installation list")
                            self._log_signal.emit("Package " +
                                                  pkg["name"] +
                                                  " has already been downloaded, moving to installation list",
                                                  logging.INFO)
                            pkg["rpms_path"] = str(paths[0])
                        paths = list(Path(debs_dir).glob(pkg["name"] + "*"))
                    if not isfile(pkg["debs_path"]):
                        if paths and fuzz.token_set_ratio(pkg["version"],
                                                          basename(str(paths[0]).
                                                                           replace(pkg["name"] + "_", "")).
                                                                  rsplit("_", 1)[0]) > 90:
                            self._msg_signal.emit("Package " +
                                                  pkg["name"] +
                                                  " has already been downloaded, moving to conversion list")
                            self._log_signal.emit("Package " +
                                                  pkg["name"] +
                                                  " has already been downloaded, moving to conversion list",
                                                  logging.INFO)
                            pkg["deb_path"] = str(paths[0])
                    if isfile(pkg_states[self._section][ppa][pkg_id]["rpm_path"]):
                        add_item_to_section("installing", pkg_states[self._section][ppa].pop(pkg_id))
                        continue
                    elif isfile(pkg_states[self._section][ppa][pkg_id]["deb_path"]):
                        add_item_to_section(self._next_section, pkg_states[self._section][ppa].pop(pkg_id))
                        continue
        cfg.write()

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
    def state_change(self):
        """Each process, download, convert, install, uninstall, must check if the package is installed
            before it continues"""
        pass

    def move_cache(self):
        """"""
        for ppa in pkg_states[self._section]:
            for pkg_id in pkg_states[self._section][ppa]:
                if isfile(pkg_states[self._section][ppa][pkg_id][self._path_name]):
                    add_item_to_section(self._next_section, pkg_states[self._section][ppa].pop(pkg_id))
                else:
                    add_item_to_section(self._error_section, pkg_states[self._section][ppa].pop(pkg_id))
            delete_ppa_if_empty(self._section, ppa)
        cfg.write()

    @staticmethod
    def check_installed(name):
        return True if len(rpm.TransactionSet().dbMatch('name', name)) else False
