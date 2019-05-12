#!/usr/bin/env python

import multiprocessing.dummy
import logging
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtGui import QBrush, QColor

import packages
from lprpm_conf import cfg, \
    pkg_states, delete_ppa_if_empty, \
    add_item_to_section, pkg_search, check_installed, \
    all_sections_not_installed
from treeview.tvmodel import TVModel
from treeview.tvitem import TVItem


class PkgTVModel(TVModel):
    list_filled_signal = pyqtSignal(list)
    list_changed_signal = pyqtSignal(str, str)
    highlight_color = QColor(255, 204, 204)
    highlight_brush = QBrush()

    def __init__(self, headers, team, arch,
                 msg_signal=None, log_signal=None, progress_signal=None,
                 transaction_progress_signal=None,
                 lock_model_signal=None, list_filling_signal=None,
                 ended_signal=None, request_action_signal=None,
                 populate_pkgs_signal=None, action_timer_signal=None):
        super(PkgTVModel, self).__init__(headers)
        self.list_filling_signal = list_filling_signal
        self.list_filled_signal.connect(self.pkg_list_complete)
        self.list_changed_signal.connect(self.list_changed)
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self._pool = multiprocessing.dummy.Pool(10)
        TVModel.highlight_brush.setColor(TVModel.highlight_color)
        TVModel.highlight_brush.setStyle(Qt.DiagCrossPattern)

        self._packages = packages.Packages(team,
                                           arch,
                                           msg_signal=msg_signal,
                                           log_signal=log_signal,
                                           progress_signal=progress_signal,
                                           transaction_progress_signal=transaction_progress_signal,
                                           lock_model_signal=lock_model_signal,
                                           list_filling_signal=list_filling_signal,
                                           ended_signal=ended_signal,
                                           request_action_signal=request_action_signal,
                                           populate_pkgs_signal=populate_pkgs_signal,
                                           action_timer_signal=action_timer_signal,
                                           list_filled_signal=self.list_filled_signal,
                                           list_changed_signal=self.list_changed_signal)

    @property
    def packages(self):
        return self._packages

    @pyqtSlot(str, str)
    def populate_pkg_list(self, ppa, arch):
        self.list_filling_signal.emit(True)
        self.removeRows(0, self.rowCount())
        if ppa is not None and arch is not None:
            self._packages.populate_pkgs(ppa.lower(), arch.lower())
        else:
            self._msg_signal.emit("The team " + str(self.packages.lp_team.name) + " has no ppas listed")
            self._log_signal.emit("This team has no ppas listed", logging.INFO)

    @pyqtSlot(str, str)
    def list_changed(self, ppa, arch):
        self.removeRows(0, self.rowCount())
        self.pkg_list_complete(self.packages.populate_pkg_list(ppa, arch))

    @pyqtSlot(list)
    def pkg_list_complete(self, pkgs):
        for pkg in pkgs:
            pkg = TVItem(pkg)
            # if pkg is installed
            if check_installed(pkg.name, pkg.version):
                # but the package isn't listed in the installed section
                p = pkg_search(['installed'], pkg.id)
                if not p:
                    p = pkg_search(all_sections_not_installed, pkg.id)
                    if p is False:
                        add_item_to_section('installed', pkg)
                    else:
                        add_item_to_section('installed', p.parent.pop(p['id']))
                pkg.installed = Qt.Checked
                self.appendRow(pkg.row)
                continue
            else:
                if pkg_search(['uninstalling'], pkg.id):
                    if check_installed(pkg.name, pkg.version):
                        pkg.installed = Qt.Unchecked
                        pkg.install_state.setBackground(Qt.red)
                        self.appendRow(pkg.row)
                    else:
                        pkg_states['uninstalling'][pkg.ppa].pop(pkg.id)
                        delete_ppa_if_empty('uninstalling', pkg.ppa)
                        continue
                if pkg_search(['tobeinstalled', 'downloading', 'converting', 'installing'], pkg.id):
                    pkg.installed = Qt.PartiallyChecked
                    self.appendRow(pkg.row)
                    continue
                else:
                    pkg.installed = Qt.Unchecked
                    self.appendRow(pkg.row)
        cfg.write()
