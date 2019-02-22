# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed_prefs_ui.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from QLabelChanged import QLabelChanged


class Ui_prefs_dialog(object):
    def setupUi(self, prefs_dialog):
        prefs_dialog.setObjectName("prefs_dialog")
        prefs_dialog.setWindowModality(QtCore.Qt.WindowModal)
        prefs_dialog.resize(400, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(prefs_dialog)
        self.buttonBox.setGeometry(QtCore.QRect(40, 260, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(prefs_dialog)
        self.label.setGeometry(QtCore.QRect(50, 130, 67, 19))
        self.label.setObjectName("label")
        self.directory_label = QLabelChanged(prefs_dialog)
        self.directory_label.setGeometry(QtCore.QRect(50, 160, 311, 19))
        self.directory_label.setAutoFillBackground(True)
        self.directory_label.setFrameShape(QtWidgets.QFrame.Box)
        self.directory_label.setObjectName("directory_label")
        self.widget = QtWidgets.QWidget(prefs_dialog)
        self.widget.setGeometry(QtCore.QRect(50, 20, 225, 89))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.checkBox = QtWidgets.QCheckBox(self.widget)
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout.addWidget(self.checkBox)
        self.checkBox_2 = QtWidgets.QCheckBox(self.widget)
        self.checkBox_2.setChecked(True)
        self.checkBox_2.setObjectName("checkBox_2")
        self.verticalLayout.addWidget(self.checkBox_2)
        self.checkBox_3 = QtWidgets.QCheckBox(self.widget)
        self.checkBox_3.setChecked(True)
        self.checkBox_3.setObjectName("checkBox_3")
        self.verticalLayout.addWidget(self.checkBox_3)

        self.retranslateUi(prefs_dialog)
        self.buttonBox.accepted.connect(prefs_dialog.accept)
        self.buttonBox.rejected.connect(prefs_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(prefs_dialog)

    def retranslateUi(self, prefs_dialog):
        _translate = QtCore.QCoreApplication.translate
        prefs_dialog.setWindowTitle(_translate("prefs_dialog", "KXFed Preferences"))
        self.label.setText(_translate("prefs_dialog", "Directory"))
        self.directory_label.setText(_translate("prefs_dialog", "TextLabel"))
        self.checkBox.setText(_translate("prefs_dialog", "Download Checked Packages"))
        self.checkBox_2.setText(_translate("prefs_dialog", "Convert Checked Packages"))
        self.checkBox_3.setText(_translate("prefs_dialog", "Install Checked Packages"))