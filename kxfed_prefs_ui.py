# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed_prefs_ui.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_prefs_dialog(object):
    def setupUi(self, prefs_dialog):
        prefs_dialog.setObjectName("prefs_dialog")
        prefs_dialog.setWindowModality(QtCore.Qt.WindowModal)
        prefs_dialog.resize(408, 403)
        self.buttonBox = QtWidgets.QDialogButtonBox(prefs_dialog)
        self.buttonBox.setGeometry(QtCore.QRect(50, 350, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(prefs_dialog)
        self.label.setGeometry(QtCore.QRect(50, 170, 151, 19))
        self.label.setObjectName("label")
        self.directory_label = QLabelChanged(prefs_dialog)
        self.directory_label.setGeometry(QtCore.QRect(50, 200, 311, 19))
        self.directory_label.setToolTip("")
        self.directory_label.setToolTipDuration(3)
        self.directory_label.setStatusTip("")
        self.directory_label.setWhatsThis("")
        self.directory_label.setAutoFillBackground(True)
        self.directory_label.setFrameShape(QtWidgets.QFrame.Box)
        self.directory_label.setObjectName("directory_label")
        self.layoutWidget = QtWidgets.QWidget(prefs_dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(50, 20, 225, 120))
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
        self.uninstall_chkbox = QtWidgets.QCheckBox(self.layoutWidget)
        self.uninstall_chkbox.setChecked(True)
        self.uninstall_chkbox.setObjectName("uninstall_chkbox")
        self.verticalLayout.addWidget(self.uninstall_chkbox)
        self.layoutWidget_2 = QtWidgets.QWidget(prefs_dialog)
        self.layoutWidget_2.setGeometry(QtCore.QRect(50, 240, 229, 61))
        self.layoutWidget_2.setObjectName("layoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.delete_downloaded_chkbox = QtWidgets.QCheckBox(self.layoutWidget_2)
        self.delete_downloaded_chkbox.setChecked(True)
        self.delete_downloaded_chkbox.setObjectName("delete_downloaded_chkbox")
        self.verticalLayout_2.addWidget(self.delete_downloaded_chkbox)
        self.delete_converted_chkbox = QtWidgets.QCheckBox(self.layoutWidget_2)
        self.delete_converted_chkbox.setChecked(True)
        self.delete_converted_chkbox.setObjectName("delete_converted_chkbox")
        self.verticalLayout_2.addWidget(self.delete_converted_chkbox)

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
        self.uninstall_chkbox.setText(_translate("prefs_dialog", "Uninstall Checked Packages"))
        self.delete_downloaded_chkbox.setText(_translate("prefs_dialog", "Delete Downloaded Packages"))
        self.delete_converted_chkbox.setText(_translate("prefs_dialog", "Delete Converted Packages"))


from qlabelchanged import QLabelChanged
