#!/usr/bin/env python

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QStandardItemModel
from packages import Packages
from kfconf import TVITEM_ROLE, cfg
from tvitem import TVItem
import multiprocessing.dummy
import subprocess

# TODO separate pkg downloading, converting and installing functions into
# TODO Packages class.  TVModel has reference to packages and Packages class
# TODO uses pyqtSignals to let the model know that it can update
# TODO that way the model can update when all packages are downloaded, handle
# TODO progressbar updates more efficiently etc. whilst keeping the implementation
# TODO details separate from the model, which is, effectively, the view.


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
        self._pool = multiprocessing.dummy.Pool(10)

    @property
    def packages(self):
        return self._packages

    def populate_pkg_list(self, ppa):
        self.list_filled.emit()
        self.removeRows(0, self.rowCount())
        self._pool.apply_async(self._packages.populate_pkgs,
                               (ppa,),
                               callback=self.pkg_list_complete)

    def pkg_list_complete(self, pkgs):
        for pkg in pkgs:
            pkg = TVItem(pkg)
            if pkg.build_link in cfg['installed']:
                pkg.installed = Qt.Checked
            else:
                pkg.installed = Qt.Unchecked
            self.appendRow(pkg.row)
        self.list_filled.emit()

    @staticmethod
    def on_item_changed(item):
        pkg = item.data(TVITEM_ROLE)
        if item.isCheckable():
            if pkg.installed == Qt.Unchecked:
                item.setCheckState(Qt.PartiallyChecked)
            if item.checkState() == Qt.Unchecked:
                if pkg.installed == Qt.PartiallyChecked:
                    cfg['tobeinstalled'][pkg.ppa].pop(pkg.id)
                    cfg.delete_ppa_if_empty('tobeinstalled', pkg.ppa)
            if item.checkState() == Qt.PartiallyChecked:
                if pkg.installed == Qt.Unchecked:
                    cfg.add_item_to_section('tobeinstalled', pkg)
                if pkg.installed == Qt.Checked:
                    cfg.add_item_to_section('tobeuninstalled', pkg)
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            pkg.installed = item.checkState()

    def action_pkgs(self):
        # uninstall packages that need uninstalling first.
        # self._packages.uninstall_pkgs()
        # install packages that need installing

        self._packages.install_pkgs()
        # TODO status bar progress report

