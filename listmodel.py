#!/usr/bin/env python

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
import multiprocessing.dummy
from packages import Packages
from config_init import cfg, cache
import subprocess


class ListItem(QStandardItem):
    def __init__(self, pkg_list, *args):
        super().__init__(*args)
        self.setCheckable(True)
        self.setEditable(False)
        self.build_link = pkg_list[0]
        self.binary_package_name = pkg_list[1]
        self.binary_package_version = pkg_list[2]
        self.resource_type_link = pkg_list[3]
        self.ppa = pkg_list[4]
        self.setText(self.binary_package_name)
        # TODO add binary_version to second column in listview
        self.setCheckState(Qt.Unchecked)
        if self.ppa in cfg['installed']:
            if self.binary_package_name in cfg['installed'][self.ppa]:
                self.setCheckState(Qt.Checked)


class ListModel(QStandardItemModel):

    list_filled = pyqtSignal()

    def __init__(self, headers, team, arch, *args):
        super().__init__(*args)
        self.__packages = Packages(team, arch)
        # self.packages.get(self._setupModelData_) do this when ppa combo is selected
        self.setHorizontalHeaderLabels(headers)
        self.__pool = multiprocessing.dummy.Pool(10)
        self.__result = None
        self.itemChanged.connect(self.on_item_changed)

    @property
    def packages(self):
        return self.__packages

    def populate_pkg_list(self, ppa):
        self.list_filled.emit()
        self.removeRows(0, self.rowCount())
        self.__result = self.__pool.apply_async(self.__packages.populate_pkgs,
                                                (ppa,),
                                                callback=self.pkg_list_complete)

    def pkg_list_complete(self, pkgs):
        for pkg in pkgs:
            self.appendRow(ListItem(pkg))

        # checkstate of pkgs that are installed
        self.list_filled.emit()

    def on_item_changed(self, item):
        if item.checkState() is Qt.Unchecked:
            if item.build_link in cfg['installed']:
                self.add_item_to_section('tobeuninstalled', item)
            elif item.uuid in cfg['tobeinstalled']:
                cfg['tobeinstalled'].pop(item.ppa)
        else:
            self.add_item_to_section('tobeinstalled', item)

    @staticmethod
    def add_item_to_section(self, section, item):
        cfg[section][item.ppa] = {}
        cfg[section][item.ppa]['build_link'] = item.build_link
        cfg[section][item.ppa]['binary_package_name'] = item.binary_package_name
        cfg[section][item.ppa]['binary_package_version'] = item.binary_package_version
        cfg[section][item.ppa]['resource_type_link'] = item.resource_type_link

    def install_btn_clicked(self):
        # uninstall packages that need uninstalling first.
        self.uninstall_pkgs()
        # install packages that need installing
        self.install_pkgs()

    def uninstall_pkgs(self, pkg):
        # get list of packages to be uninstalled from cfg, using pop to delete
        for ppa in cfg['tobeuninstalled']:
            for pkg in cfg['tobeuninstalled'][ppa]:
                subprocess.run(['pkexec','./uninstall_pkg', pkg.binary_name], stdout=subprocess.PIPE)
        cfg['tobeuninstalled'].clear()

    def install_pkgs(self):
        # get list of packages to be installed from cfg, using pop to delete
        for ppa in cfg['tobeinstalled']:
            for pkg in cfg['tobeinstalled'][ppa]:
                subprocess.run(['pkexec', './install_pkg', pkg.rpm_file], stdout=subprocess.PIPE)
        cfg['tobeinstalled'].clear()
