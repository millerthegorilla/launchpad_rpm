# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfedmsgsdialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from messageswindow import MessagesWindow

class Ui_KxfedMsgsDialog(object):
    def setupUi(self, KxfedMsgsDialog):
        KxfedMsgsDialog.setObjectName("KxfedMsgsDialog")
        KxfedMsgsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        KxfedMsgsDialog.resize(450, 330)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(KxfedMsgsDialog.sizePolicy().hasHeightForWidth())
        KxfedMsgsDialog.setSizePolicy(sizePolicy)
        self.gridLayout = QtWidgets.QGridLayout(KxfedMsgsDialog)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.plainTextEdit = MessagesWindow(KxfedMsgsDialog)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout.addWidget(self.plainTextEdit)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton = QtWidgets.QPushButton(KxfedMsgsDialog)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(KxfedMsgsDialog)
        QtCore.QMetaObject.connectSlotsByName(KxfedMsgsDialog)

    def retranslateUi(self, KxfedMsgsDialog):
        _translate = QtCore.QCoreApplication.translate
        KxfedMsgsDialog.setWindowTitle(_translate("KxfedMsgsDialog", "KxfedMsgsDialog"))
        self.pushButton.setText(_translate("KxfedMsgsDialog", "Close"))
