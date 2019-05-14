#!/usr/bin/env python
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem

TVITEM_ROLE = Qt.UserRole + 1
TEAMNAME_ROLE = Qt.UserRole + 2
PPA_ROLE = Qt.UserRole + 3


class TVItem:
    def __init__(self, pkg_list):
        """pkg_list is a list:
          [i.build_link,
           ppa,
           i.binary_package_name,
           i.binary_package_version,
           self.lp_team.display_name,
           self.lp_team.name,
           uuid.uuid4().urn]"""
        self._deb_path = ""
        self._rpm_path = ""
        self._deb_link = ""
        self._build_link = pkg_list[0]
        self._ppa = pkg_list[1]
        self._installed = Qt.Unchecked
        self._install_state = QStandardItem()
        self._install_state.__lt__ = self.less_than
        self._install_state.setData(self, role=TVITEM_ROLE)
        self._install_state.setCheckable(True)
        # self._install_state.setEditable(False)
        self._install_state.setTristate(True)
        self._install_state.setCheckState(Qt.Unchecked)
        self._name = QStandardItem(pkg_list[2])
        self._name.setData(self, role=TVITEM_ROLE)
        self._version = QStandardItem(pkg_list[3])
        self._version.setData(self, role=TVITEM_ROLE)
        self._team_display_name = QStandardItem(pkg_list[4])
        self._team_name = pkg_list[5]
        self._team_display_name.setData(self._team_name, role=TEAMNAME_ROLE)
        self._team_display_name.setData(self._ppa, role=PPA_ROLE)
        self._row = [self._install_state, self._name, self._version, self._team_display_name]
        # self._id = uuid.uuid4().urn
        self._id = pkg_list[6]

    @property
    def build_link(self):
        return self._build_link

    @property
    def name(self):
        return self._name.text()

    @property
    def version(self):
        return self._version.text()

    @property
    def ppa(self):
        return self._ppa

    @property
    def team(self):
        return self._team_name

    @property
    def installed(self):
        return self._installed

    @installed.setter
    def installed(self, s):
        if s in [Qt.Unchecked, Qt.PartiallyChecked, Qt.Checked]:
            self._installed = s
            self._install_state.setCheckState(s)
        else:
            raise TypeError("property must be Qt.checkstate")

    @property
    def row(self):
        return self._row

    @property
    def deb_link(self):
        return self._deb_link

    @property
    def deb_path(self):
        return self._deb_path

    @property
    def rpm_path(self):
        return self._rpm_path

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, i):
        self._id = i

    @property
    def install_state(self):
        return self._install_state

    def less_than(self, other):
        return self._install_state.checkState() > other.checkState()
