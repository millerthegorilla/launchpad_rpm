# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'assets/lprpm_msgsdialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets
from ui.messageswindow import MessagesWindow


class UiLPRpmMsgsDialog(object):
    def setupUi(self, LPRpmMsgsDialog):
        LPRpmMsgsDialog.setObjectName("LPRpmMsgsDialog")
        LPRpmMsgsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        LPRpmMsgsDialog.resize(450, 330)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LPRpmMsgsDialog.sizePolicy().hasHeightForWidth())
        LPRpmMsgsDialog.setSizePolicy(sizePolicy)
        self.gridLayout = QtWidgets.QGridLayout(LPRpmMsgsDialog)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.plainTextEdit = MessagesWindow(LPRpmMsgsDialog)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout.addWidget(self.plainTextEdit)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton = QtWidgets.QPushButton(LPRpmMsgsDialog)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(LPRpmMsgsDialog)
        QtCore.QMetaObject.connectSlotsByName(LPRpmMsgsDialog)

    def retranslateUi(self, LPRpmMsgsDialog):
        _translate = QtCore.QCoreApplication.translate
        LPRpmMsgsDialog.setWindowTitle(_translate("LPRpmMsgsDialog", "LPRpmMsgsDialog"))
        self.pushButton.setText(_translate("LPRpmMsgsDialog", "Close"))

