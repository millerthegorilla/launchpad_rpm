#!/usr/bin/env python

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant;
from PyQt5.QtGui import QStandardItem, QStandardItemModel;


class TreeItem(QStandardItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCheckable(True)
        self.setEditable(False)
        self.setCheckState(Qt.UnChecked)

class TreeModel(QStandardItemModel):
    def __init__(self, headers, packages, **kwargs):
        super().__init__()
        self.__packages = packages
        #self.packages.get(self._setupModelData_) do this when ppa combo is selected
        self.setHorizontalHeaderLabels(headers)

    @property
    def packages(self):
        return self.__packages

    def _setupModelData_(self):
        pass
