# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'assets/lprpm_first_run_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class UiLPRpmFirstRunDialog(object):
    def setupUi(self, LPRpmFirstRunDialog):
        LPRpmFirstRunDialog.setObjectName("LPRpmFirstRunDialog")
        LPRpmFirstRunDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        LPRpmFirstRunDialog.resize(410, 126)
        self.progressBar = QtWidgets.QProgressBar(LPRpmFirstRunDialog)
        self.progressBar.setGeometry(QtCore.QRect(10, 10, 391, 61))
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.label = QtWidgets.QLabel(LPRpmFirstRunDialog)
        self.label.setGeometry(QtCore.QRect(10, 60, 391, 51))
        self.label.setWordWrap(True)
        self.label.setObjectName("label")

        self.retranslateUi(LPRpmFirstRunDialog)
        QtCore.QMetaObject.connectSlotsByName(LPRpmFirstRunDialog)

    def retranslateUi(self, LPRpmFirstRunDialog):
        _translate = QtCore.QCoreApplication.translate
        LPRpmFirstRunDialog.setWindowTitle(_translate("LPRpmFirstRunDialog", "LPRPMLaunchpad - First Run"))
        self.label.setText(_translate("LPRpmFirstRunDialog", "TextLabel"))
