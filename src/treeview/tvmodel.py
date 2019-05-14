#!/usr/bin/env python

import os
import logging
from PyQt5.QtCore import pyqtSignal, Qt, QObject
from PyQt5.QtGui import QStandardItemModel, QBrush, QColor

from lprpm_conf import cfg, \
    config_dir, CONFIG_FILE, \
    pkg_states, delete_ppa_if_empty, \
    add_item_to_section, pkg_search, delete_team_if_empty, \
    all_sections_not_installed
from treeview.tvitem import TVITEM_ROLE


class TVModel(QStandardItemModel):
    list_filled_signal = pyqtSignal(list)
    list_changed_signal = pyqtSignal(str, str)
    clear_brush = None
    highlight_color = QColor(255, 204, 204)
    highlight_brush = QBrush()

    def __init__(self, headers):
        super(TVModel, self).__init__()
        # self.itemChanged.connect(TVModel.on_item_changed)
        # can't get overriding to work
        super().itemChanged.connect(self.itemChanged)
        TVModel.highlight_brush.setColor(TVModel.highlight_color)
        TVModel.highlight_brush.setStyle(Qt.DiagCrossPattern)
        self.setHorizontalHeaderLabels(headers)

    def sort(self, p_int, order=None):
        super(TVModel, self).sort(p_int, order)

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
        # item = QStandardItem(item)
        try:
            super().itemChanged.disconnect()
            pkg = item.data(TVITEM_ROLE)
            if item.isCheckable():
                # if item is not installed
                if pkg.installed == Qt.Unchecked:
                    item.setCheckState(Qt.PartiallyChecked)
                # if item was installed and is now to be uninstalled
                if item.checkState() == Qt.Unchecked:
                    # if item is in the process of being installed
                    # and has been cancelled
                    try:
                        if pkg.installed == Qt.PartiallyChecked:
                            if pkg.team in pkg_states['tobeinstalled']:
                                if pkg.ppa in pkg_states['tobeinstalled'][pkg.team]:
                                    if pkg.id in pkg_states['tobeinstalled'][pkg.team][pkg.ppa]:
                                        pkg_states['tobeinstalled'][pkg.team][pkg.ppa].pop(pkg.id)
                                        delete_ppa_if_empty('tobeinstalled', pkg.team, pkg.ppa)
                                        delete_team_if_empty('tobeinstalled', pkg.team)
                            if pkg.team in pkg_states['downloading']:
                                if pkg.ppa in pkg_states['downloading'][pkg.team]:
                                    if pkg.id in pkg_states['downloading'][pkg.team][pkg.ppa]:
                                        for deb_path in pkg_states['downloading'][pkg.team][pkg.ppa][pkg.id]:
                                            if os.path.exists(deb_path) and cfg['delete_downloaded'] == 'True':
                                                os.remove(deb_path)
                                        pkg_states['downloading'][pkg.team][pkg.ppa].pop(pkg.id)
                                        delete_ppa_if_empty('downloading', pkg.team, pkg.ppa)
                                        delete_team_if_empty('downloading', pkg.team)
                            if pkg.team in pkg_states['converting']:
                                if pkg.ppa in pkg_states['converting'][pkg.team]:
                                    if pkg.id in pkg_states['converting'][pkg.team][pkg.ppa]:
                                        for deb_path in pkg_states['converting'][pkg.team][pkg.ppa][pkg.id]:
                                            if os.path.exists(deb_path) and cfg['delete_downloaded'] == 'True':
                                                os.remove(deb_path)
                                        pkg_states['converting'][pkg.team][pkg.ppa].pop(pkg.id)
                                        delete_ppa_if_empty('converting', pkg.team, pkg.ppa)
                                        delete_team_if_empty('converting', pkg.team)
                            if pkg.team in pkg_states['installing']:
                                if pkg.ppa in pkg_states['installing'][pkg.team]:
                                    if pkg.id in pkg_states['installing'][pkg.team][pkg.ppa]:
                                        deb_path = pkg_states['installing'][pkg.team][pkg.ppa][pkg.id]['deb_path']
                                        if os.path.isfile(deb_path) and cfg['delete_downloaded'] == 'True':
                                            os.remove(deb_path)
                                        rpm_path = pkg_states['installing'][pkg.team][pkg.ppa][pkg.id]['rpm_path']
                                        if os.path.isfile(rpm_path) and cfg['delete_converted'] == 'True':
                                            os.remove(rpm_path)
                                        pkg_states['installing'][pkg.team][pkg.ppa].pop(pkg.id)
                                        delete_ppa_if_empty('installing', pkg.team, pkg.ppa)
                                        delete_team_if_empty('installing', pkg.team)
                    except IsADirectoryError as e:
                        self.packages.log_signal.emit('Error in config ' + str(e), logging.CRITICAL)
                    # if item is being set to uninstall
                    if pkg.installed == Qt.Checked:
                        # move from installed to uninstalling section
                        section = pkg_search(['uninstalling'], pkg.id)
                        if section:
                            # installed window has changed
                            item.setBackground(QBrush(Qt.red))
                        section = pkg_search(['installed'], pkg.id)
                        if section:
                            pkg_states['installed'][pkg.team][pkg.ppa].pop(pkg.id)
                            delete_ppa_if_empty('installed', pkg.team, pkg.ppa)
                            delete_team_if_empty('installed', pkg.team)
                            add_item_to_section('uninstalling', pkg)
                            item.setBackground(QBrush(Qt.red))
                # item is to be downloaded/converted
                if item.checkState() == Qt.Checked:
                    # ie item was partially checked and user clicked it
                    if pkg.installed != Qt.Checked:
                        # the pkg.installed check here is for the sake of the installed table
                        item.setCheckState(Qt.Unchecked)
                        found_pkg = pkg_search(all_sections_not_installed, pkg.id)
                        section = found_pkg.parent.parent.name
                        ppa = found_pkg.parent.name
                        team = found_pkg.parent.parent.name
                        pkg_states[section][team][ppa].pop(found_pkg['id'])
                        delete_ppa_if_empty(section, team, ppa)
                        delete_team_if_empty(section, team)
                    else:
                        # so the installed table has been checked again and the pkgtable needs adjusting
                        item.setBackground(QBrush(Qt.color0))
                if item.checkState() == Qt.PartiallyChecked:
                    # but if the pkg wasn't downloaded/converted yet
                    if pkg.installed == Qt.Unchecked:
                        if item.background().color() == Qt.red:
                            pkg_states['uninstalling'][pkg.team][pkg.ppa].pop(pkg.id)
                            delete_ppa_if_empty('uninstalling', pkg.team, pkg.ppa)
                            delete_team_if_empty('uninstalling', pkg.team)
                            add_item_to_section('installed', pkg)
                            item.setCheckState(Qt.Checked)
                            item.setBackground(Qt.color0)
                        else:
                            cfg.add_item_to_section('tobeinstalled', pkg)
                    # or item is to be uninstalled
                    if pkg.installed == Qt.Checked:
                        pkg_states['installed'][pkg.team][pkg.ppa].pop(pkg.id)
                        delete_ppa_if_empty('installed', pkg.team, pkg.ppa)
                        delete_team_if_empty('installed', pkg.team)
                        cfg.add_item_to_section('tobeuninstalled', pkg)
                        item.setBackground(QBrush(Qt.red))
                pkg.installed = item.checkState()
            cfg.filename = config_dir + CONFIG_FILE
            cfg.write()
            super().itemChanged.connect(self.itemChanged)
        except KeyError as e:
            super().itemChanged.connect(self.itemChanged)
        except Exception as e:
            pass

