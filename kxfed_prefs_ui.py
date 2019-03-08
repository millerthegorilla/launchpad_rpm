# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed_prefs_ui.ui'
#
# Created by: PyQt5 UI code generator 5.12
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
        self.label.setGeometry(QtCore.QRect(50, 130, 151, 19))
        self.label.setObjectName("label")
        self.directory_label = QLabelChanged(prefs_dialog)
        self.directory_label.setGeometry(QtCore.QRect(50, 160, 311, 19))
        self.directory_label.setToolTip("The directories that store the deb and rpm files are located here, as well as the temporary conversion files")
        self.directory_label.setStatusTip("")
        self.directory_label.setWhatsThis("")
        self.directory_label.setAutoFillBackground(True)
        self.directory_label.setFrameShape(QtWidgets.QFrame.Box)
        self.directory_label.setObjectName("directory_label")
        self.layoutWidget = QtWidgets.QWidget(prefs_dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(50, 20, 225, 89))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.download_chkbox = QtWidgets.QCheckBox(self.layoutWidget)
        self.download_chkbox.setChecked(True)
        self.download_chkbox.setObjectName("download_chkbox")
        self.verticalLayout.addWidget(self.download_chkbox)
        self.convert_chkbox = QtWidgets.QCheckBox(self.layoutWidget)
        self.convert_chkbox.setChecked(True)
        self.convert_chkbox.setObjectName("convert_chkbox")
        self.verticalLayout.addWidget(self.convert_chkbox)
        self.install_chkbox = QtWidgets.QCheckBox(self.layoutWidget)
        self.install_chkbox.setChecked(True)
        self.install_chkbox.setObjectName("install_chkbox")
        self.verticalLayout.addWidget(self.install_chkbox)

        self.retranslateUi(prefs_dialog)
        self.buttonBox.accepted.connect(prefs_dialog.accept)
        self.buttonBox.rejected.connect(prefs_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(prefs_dialog)

    def retranslateUi(self, prefs_dialog):
        _translate = QtCore.QCoreApplication.translate
        prefs_dialog.setWindowTitle(_translate("prefs_dialog", "KXFed Preferences"))
        self.label.setText(_translate("prefs_dialog", "Working Directory"))
        self.directory_label.setText(_translate("prefs_dialog", "TextLabel"))
        self.download_chkbox.setText(_translate("prefs_dialog", "Download Checked Packages"))
        self.convert_chkbox.setText(_translate("prefs_dialog", "Convert Checked Packages"))
        self.install_chkbox.setText(_translate("prefs_dialog", "Install Checked Packages"))


