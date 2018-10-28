# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        MainWindow.resize(459, 521)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.formLayout = QtWidgets.QFormLayout(self.centralwidget)
        self.formLayout.setObjectName("formLayout")
        self.team_label = QtWidgets.QLabel(self.centralwidget)
        self.team_label.setObjectName("team_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.team_label)
        self.team_combo = QtWidgets.QComboBox(self.centralwidget)
        self.team_combo.setObjectName("team_combo")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.team_combo)
        self.arch_label = QtWidgets.QLabel(self.centralwidget)
        self.arch_label.setObjectName("arch_label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.arch_label)
        self.arch_combo = QtWidgets.QComboBox(self.centralwidget)
        self.arch_combo.setObjectName("arch_combo")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.arch_combo)
        self.ppa_label = QtWidgets.QLabel(self.centralwidget)
        self.ppa_label.setObjectName("ppa_label")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.ppa_label)
        self.ppa_combo = QtWidgets.QComboBox(self.centralwidget)
        self.ppa_combo.setObjectName("ppa_combo")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.ppa_combo)
        self.packages_label = QtWidgets.QLabel(self.centralwidget)
        self.packages_label.setObjectName("packages_label")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.packages_label)
        self.packages_treeview = QtWidgets.QTreeView(self.centralwidget)
        self.packages_treeview.setObjectName("packages_treeview")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.SpanningRole, self.packages_treeview)
        self.kernelbuild_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.kernelbuild_chk.setObjectName("kernelbuild_chk")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.SpanningRole, self.kernelbuild_chk)
        self.lowlatency_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.lowlatency_chk.setObjectName("lowlatency_chk")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.lowlatency_chk)
        self.install_btn = QtWidgets.QPushButton(self.centralwidget)
        self.install_btn.setObjectName("install_btn")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.SpanningRole, self.install_btn)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.team_label.setText(_translate("MainWindow", "Team :"))
        self.team_combo.setItemText(0, _translate("MainWindow", "KxStudio-Debian"))
        self.arch_label.setText(_translate("MainWindow", "Arch :"))
        self.arch_combo.setItemText(0, _translate("MainWindow", "AMD64"))
        self.arch_combo.setItemText(1, _translate("MainWindow", "X386"))
        self.ppa_label.setText(_translate("MainWindow", "PPA :"))
        self.packages_label.setText(_translate("MainWindow", "Packages: "))
        self.kernelbuild_chk.setText(_translate("MainWindow", "Build and install latest RT kernel"))
        self.lowlatency_chk.setText(_translate("MainWindow", "Lowlatency"))
        self.install_btn.setText(_translate("MainWindow", "Install"))

