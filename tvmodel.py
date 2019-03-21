#!/usr/bin/env python

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QStandardItemModel
from packages import Packages
import kfconf
from tvitem import TVItem
import multiprocessing.dummy
from PyQt5.QtCore import pyqtSlot


class TVModel(QStandardItemModel):
    list_filled = pyqtSignal()
    message = pyqtSignal(str)
    exception = pyqtSignal('PyQt_PyObject')

    def __init__(self, headers, team, arch):
        super().__init__()
        self._packages = Packages(team, arch)
        # self.packages.get(self._setupModelData_) do this when ppa combo is selected
        self.setHorizontalHeaderLabels(headers)
        self.itemChanged.connect(TVModel.on_item_changed)
        self.packages.pkg_list_complete.connect(self.pkg_list_complete)
        self._pool = multiprocessing.dummy.Pool(10)

    @property
    def packages(self):
        return self._packages

    def populate_pkg_list(self, ppa, arch):
        self.list_filled.emit()
        self.removeRows(0, self.rowCount())
        self._packages.populate_pkgs(ppa.lower(), arch.lower())

    @pyqtSlot(list)
    def pkg_list_complete(self, pkgs):
        for pkg in pkgs:
            pkg = TVItem(pkg)
            kfconf.cfg['found'] = {}
            kfconf.cfg['installed'].walk(kfconf.config_search, search_value=str(pkg.build_link) + "***" + str(pkg.name))
            if kfconf.cfg['found']:
                pkg.installed = Qt.Checked
                self.appendRow(pkg._row)
                kfconf.cfg['found'] = {}
                continue
            kfconf.cfg['tobeinstalled'].walk(kfconf.config_search, search_value=str(pkg.build_link) + "***" + str(pkg.name))
            if not kfconf.cfg['found']:
                kfconf.cfg['downloading'].walk(kfconf.config_search, search_value=str(pkg.build_link) + "***" + str(pkg.name))
            if not kfconf.cfg['found']:
                kfconf.cfg['converting'].walk(kfconf.config_search, search_value=str(pkg.build_link) + "***" + str(pkg.name))
            if not kfconf.cfg['found']:
                kfconf.cfg['installing'].walk(kfconf.config_search, search_value=str(pkg.build_link) + "***" + str(pkg.name))
            if kfconf.cfg['found']:
                pkg.installed = Qt.PartiallyChecked
                self.appendRow(pkg.row)
                kfconf.cfg['found'] = {}
                continue
            else:
                pkg.installed = Qt.Unchecked
                self.appendRow(pkg._row)
        self.list_filled.emit()

    @staticmethod
    def on_item_changed(item):
        # item is tristate
        # unchecked = not installed
        # partially checked = in the process of being installed
        #                     ie downloaded/converted/installing but not installed
        # checked = installed
        pkg = item.data(kfconf.TVITEM_ROLE)
        if item.isCheckable():
            # if item is not installed
            if pkg.installed == Qt.Unchecked:
                item.setCheckState(Qt.PartiallyChecked)
            # if item was installed and is now to be uninstalled
            if item.checkState() == Qt.Unchecked:
                # if item is in the process of being installed
                # and has been cancelled
                if pkg.installed == Qt.PartiallyChecked:
                    kfconf.cfg['tobeinstalled'][pkg.ppa].pop(pkg.id)
                    kfconf.cfg.delete_ppa_if_empty('tobeinstalled', pkg.ppa)
                    # need further logic here to delete downloaded/converted pkgs
            # item is to be downloaded/converted
            if item.checkState() == Qt.PartiallyChecked:
                # but if the pkg wasn't downloaded/converted yet
                if pkg.installed == Qt.Unchecked:
                    kfconf.cfg.add_item_to_section('tobeinstalled', pkg)
                # or item is to be uninstalled
                if pkg.installed == Qt.Checked:
                    kfconf.cfg.add_item_to_section('tobeuninstalled', pkg)
            pkg.installed = item.checkState()
        kfconf.cfg.filename = kfconf.config_dir + kfconf.CONFIG_FILE
        kfconf.cfg.write()
