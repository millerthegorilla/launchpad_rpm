#!/usr/bin/env python

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QObject
from PyQt5.QtGui import QStandardItemModel, QBrush, QColor
from kfconf import cfg, TVITEM_ROLE, config_dir, CONFIG_FILE
from tvitem import TVItem
import kfconf
import multiprocessing.dummy
import packages


class TVModel(QStandardItemModel, QObject):

    #list_filling = pyqtSignal()
    list_filled_signal = pyqtSignal(list)
    clear_brush = None
    highlight_color = QColor(255, 204, 204)
    highlight_brush = QBrush()
    #itemChanged = pyqtSignal(QStandardItem)

    def __init__(self, headers, team, arch,
                 msg_signal, log_signal, progress_signal,
                 transaction_progress_signal,
                 lock_model_signal, list_filling_signal, cancel_signal):
        super().__init__()
        self.list_filling_signal = list_filling_signal
        self.list_filled_signal.connect(self.pkg_list_complete)
        self._packages = packages.Packages(team,
                                           arch,
                                           msg_signal,
                                           log_signal,
                                           progress_signal,
                                           transaction_progress_signal,
                                           lock_model_signal,
                                           list_filling_signal,
                                           cancel_signal,
                                           self.list_filled_signal)
        # # self.packages.get(self._setupModelData_) do this when ppa combo is selected
        self.setHorizontalHeaderLabels(headers)
        #self.itemChanged.connect(TVModel.on_item_changed)
        # can't get overriding to work
        super().itemChanged.connect(self.itemChanged)
        #kxfed.MainW.list_filled.connect(self.pkg_list_complete)
        self._pool = multiprocessing.dummy.Pool(10)
        TVModel.highlight_brush.setColor(TVModel.highlight_color)
        TVModel.highlight_brush.setStyle(Qt.DiagCrossPattern)

    @property
    def packages(self):
        return self._packages

    def populate_pkg_list(self, ppa, arch):
        self.removeRows(0, self.rowCount())
        self._packages.populate_pkgs(ppa.lower(), arch.lower())

    @pyqtSlot(list)
    def pkg_list_complete(self, pkgs):
        for pkg in pkgs:
            pkg = TVItem(pkg)
            cfg['found'] = {}
            if self.packages.pkg_search(['installed'], pkg.id):
                pkg.installed = Qt.Checked
                self.appendRow(pkg._row)
                continue
            if self.packages.pkg_search(['tobeinstalled', 'downloading', 'converting', 'installing'], pkg.id):
                pkg.installed = Qt.PartiallyChecked
                self.appendRow(pkg.row)
                continue
            else:
                pkg.installed = Qt.Unchecked
                self.appendRow(pkg._row)
        self.list_filling_signal.emit()

    def itemChanged(self, item):
        # I tried overloaded itemChanged, and also connecting itemChanged
        # to this function, but unless it was static it wouldn't work
        # update - I connected to super's itemChanged, and it works properly
        # now
        # item is tristate
        # unchecked = not installed
        # unchecked but highlighted row - uninstalling
        # partially checked = in the process of being installed
        #                     ie downloaded/converted/installing but not installed
        # checked = installed
        #item = QStandardItem(item)
        pkg = item.data(TVITEM_ROLE)
        if item.isCheckable():
            # if item is not installed
            if pkg.installed == Qt.Unchecked:
                item.setCheckState(Qt.PartiallyChecked)
            # if item was installed and is now to be uninstalled
            if item.checkState() == Qt.Unchecked:
                # if item is in the process of being installed
                # and has been cancelled
                if pkg.installed == Qt.PartiallyChecked:
                    kfconf.pkg_states['tobeinstalled'][pkg.ppa].pop(pkg.id)
                    cfg.delete_ppa_if_empty('tobeinstalled', pkg.ppa)
                    # need further logic here to delete downloaded/converted pkgs
            # item is to be downloaded/converted
            if item.checkState() == Qt.PartiallyChecked:
                # but if the pkg wasn't downloaded/converted yet
                if pkg.installed == Qt.Unchecked:
                    cfg.add_item_to_section('tobeinstalled', pkg)
                # or item is to be uninstalled
                if pkg.installed == Qt.Checked:
                    cfg.add_item_to_section('tobeuninstalled', pkg)
                    TVModel.clear_brush = item.background()
                    item.setBackground(TVModel.highlight_brush)
            if item.checkState() == Qt.Checked:
                item.setCheckState(pkg.installed)
            pkg.installed = item.checkState()
        cfg.filename = config_dir + CONFIG_FILE
        cfg.write()
