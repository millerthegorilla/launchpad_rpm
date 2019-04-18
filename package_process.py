from abc import abstractmethod
import rpm
from kfconf import pkg_states, cfg, add_item_to_section, delete_ppa_if_empty
from os.path import isfile
from collections import namedtuple


class PackageProcess(list):
    """An abstract base class that extends also from list. The abstract methods define an interface
        that must be implemented by the sub classes"""
    def __init__(self, *args):
        super(PackageProcess, self).__init__(args)
        self._section = ""
        self._error_section = ""
        self._next_section = ""
        self._path_name = ""
        self._pkg_tuple = namedtuple("pkg_tuple", ["ppa", "pkg"])

    def read_section(self):
        """Reads the section from the cache as a list of packages (self)."""
        for ppa in pkg_states[self._section]:
            for pkgid in pkg_states[self._section][ppa]:
                self.append(self._pkg_tuple(ppa=ppa, pkg=pkg_states[self._section][ppa][pkgid]))

    @abstractmethod
    def state_change(self):
        """Each process, download, convert, install, uninstall, must check if the package is installed
            before it continues"""
        pass

    def move_cache(self):
        """"""
        for ppa in pkg_states[self._section]:
            for pkg_id in pkg_states[self._section][ppa]:
                if isfile(pkg_states[self._section][ppa][pkg_id][self._path_type]):
                    add_item_to_section(self._next_section, pkg_states[self._section][ppa].pop(pkg_id))
                else:
                    add_item_to_section(self._error_section, pkg_states[self._section][ppa].pop(pkg_id))
        cfg.write()
        delete_ppa_if_empty(self._section)

    @staticmethod
    def check_installed(name):
        return True if len(rpm.TransactionSet().dbMatch('name', name)) else False

    @staticmethod
    def pkg_search(sections, search_value):
        """sections is a list of strings - names of sections - to search
           search value is content string"""
        for section in sections:
            for ppa in pkg_states[section]:
                for pkg_id in pkg_states[section][ppa]:
                    if search_value in pkg_states[section][ppa][pkg_id].dict().values():
                        return pkg_states[section][ppa][pkg_id]
        return False





