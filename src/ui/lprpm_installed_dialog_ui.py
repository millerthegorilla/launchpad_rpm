# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'assets/lprpm_installed.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class UiLPRpmInstalledDialog(object):
    def setupUi(self, LPRpmInstalledDialog):
        LPRpmInstalledDialog.setObjectName("LPRpmInstalledDialog")
        LPRpmInstalledDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        LPRpmInstalledDialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(LPRpmInstalledDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableView = QtWidgets.QTableView(LPRpmInstalledDialog)
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)
        self.buttonBox = QtWidgets.QDialogButtonBox(LPRpmInstalledDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.raise_()
        self.tableView.raise_()

        self.retranslateUi(LPRpmInstalledDialog)
        self.buttonBox.rejected.connect(LPRpmInstalledDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(LPRpmInstalledDialog)

    def retranslateUi(self, LPRpmInstalledDialog):
        _translate = QtCore.QCoreApplication.translate
        LPRpmInstalledDialog.setWindowTitle(_translate("LPRpmInstalledDialog", "Installed Packages"))
