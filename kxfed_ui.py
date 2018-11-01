# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed_ui.ui'
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
        self.team_label = QtWidgets.QLabel(self.centralwidget)
        self.team_label.setGeometry(QtCore.QRect(9, 9, 44, 20))
        self.team_label.setObjectName("team_label")
        self.team_combo = QtWidgets.QComboBox(self.centralwidget)
        self.team_combo.setEnabled(False)
        self.team_combo.setGeometry(QtCore.QRect(78, 9, 221, 28))
        self.team_combo.setEditable(False)
        self.team_combo.setObjectName("team_combo")
        self.arch_label = QtWidgets.QLabel(self.centralwidget)
        self.arch_label.setGeometry(QtCore.QRect(9, 43, 38, 20))
        self.arch_label.setObjectName("arch_label")
        self.arch_combo = QtWidgets.QComboBox(self.centralwidget)
        self.arch_combo.setGeometry(QtCore.QRect(78, 43, 221, 28))
        self.arch_combo.setObjectName("arch_combo")
        self.ppa_label = QtWidgets.QLabel(self.centralwidget)
        self.ppa_label.setGeometry(QtCore.QRect(9, 77, 34, 20))
        self.ppa_label.setObjectName("ppa_label")
        self.ppa_combo = QtWidgets.QComboBox(self.centralwidget)
        self.ppa_combo.setEnabled(True)
        self.ppa_combo.setGeometry(QtCore.QRect(78, 77, 221, 28))
        self.ppa_combo.setObjectName("ppa_combo")
        self.packages_label = QtWidgets.QLabel(self.centralwidget)
        self.packages_label.setGeometry(QtCore.QRect(9, 111, 68, 20))
        self.packages_label.setObjectName("packages_label")
        self.kernelbuild_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.kernelbuild_chk.setGeometry(QtCore.QRect(10, 396, 234, 26))
        self.kernelbuild_chk.setObjectName("kernelbuild_chk")
        self.lowlatency_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.lowlatency_chk.setGeometry(QtCore.QRect(10, 428, 101, 26))
        self.lowlatency_chk.setObjectName("lowlatency_chk")
        self.install_btn = QtWidgets.QPushButton(self.centralwidget)
        self.install_btn.setGeometry(QtCore.QRect(10, 460, 80, 28))
        self.install_btn.setObjectName("install_btn")
        self.pkgs_listView = QtWidgets.QListView(self.centralwidget)
        self.pkgs_listView.setGeometry(QtCore.QRect(9, 129, 441, 261))
        self.pkgs_listView.setObjectName("pkgs_listView")
        self.load_label = QtWidgets.QLabel(self.centralwidget)
        self.load_label.setGeometry(QtCore.QRect(-60, 220, 571, 51))
        font = QtGui.QFont()
        font.setPointSize(50)
        self.load_label.setFont(font)
        self.load_label.setScaledContents(False)
        self.load_label.setAlignment(QtCore.Qt.AlignCenter)
        self.load_label.setObjectName("load_label")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "KXFed - KXStudio on Fedora"))
        self.team_label.setText(_translate("MainWindow", "Team :"))
        self.arch_label.setText(_translate("MainWindow", "Arch :"))
        self.ppa_label.setText(_translate("MainWindow", "PPA :"))
        self.packages_label.setText(_translate("MainWindow", "Packages: "))
        self.kernelbuild_chk.setText(_translate("MainWindow", "Build and install latest RT kernel"))
        self.lowlatency_chk.setText(_translate("MainWindow", "Lowlatency"))
        self.install_btn.setText(_translate("MainWindow", "Install"))
        self.load_label.setText(_translate("MainWindow", "loading..."))

