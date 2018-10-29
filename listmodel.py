#!/usr/bin/env python

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
import multiprocessing.dummy
import logging


class ListItem(QStandardItem):
    def __init__(self, pkg_list, *args):
        super().__init__(*args)
        self.setCheckable(True)
        self.setEditable(False)
        self.__build_link = pkg_list[0]
        self.__binary_package_name = pkg_list[1]
        self.__binary_package_version = pkg_list[2]
        self.__resource_type_link = pkg_list[3]
        self.setText(self.__binary_package_name)
        self.setCheckState(False)


class ListModel(QStandardItemModel):

    list_filled = pyqtSignal(bool)

    def __init__(self, headers, packages, *args):
        super().__init__(*args)
        self.__packages = packages
        # self.packages.get(self._setupModelData_) do this when ppa combo is selected
        self.setHorizontalHeaderLabels(headers)
        self.__pool = multiprocessing.dummy.Pool(10)
        self.__result = None

    @property
    def packages(self):
        return self.__packages

    def populate_pkg_list(self, ppa):
        self.__list_filled.emit(False)
        self.removeRows(0, self.rowCount())
        # self.__pool.terminate()
        self.__packages.ppa = ppa
        self.__result = self.__pool.apply_async(self.__packages.populate_pkgs, callback=self.fill_list)

    def fill_list(self, pkgs):
        print(pkgs)
        for pkg in pkgs:
            self.appendRow(QStandardItem(ListItem(pkg)))
        self.__list_filled.emit(True)



