#!/usr/bin/env python
from PyQt5.QtGui import QStandardItem
from PyQt5.QtCore import Qt
import uuid
from kfconf import TVITEM_ROLE


class TVItem:
    def __init__(self, pkg_list):
        self._deb_link = ""
        self._build_link = pkg_list[0]
        self._ppa = pkg_list[1]
        self._installed = Qt.Unchecked
        self._install_state = QStandardItem(Qt.Unchecked)
        self._install_state.setCheckable(True)
        # self._install_state.setEditable(False)
        self._install_state.setTristate(True)
        self._install_state.setData(self, role=TVITEM_ROLE)
        self._name = QStandardItem(pkg_list[2])
        self._name.setData(self, role=TVITEM_ROLE)
        self._version = QStandardItem(pkg_list[3])
        self._version.setData(self, role=TVITEM_ROLE)
        self._row = [self._install_state, self._name, self._version]
        self._id = uuid.uuid4().urn

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
    def installed(self):
        return self._installed

    @installed.setter
    def installed(self, s):
        self._installed = s

    @property
    def row(self):
        return self._row

    @property
    def deb_link(self):
        return self._deb_link

    @property
    def id(self):
        return self._id
