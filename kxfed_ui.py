# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed_ui.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        MainWindow.resize(459, 612)
        MainWindow.setMinimumSize(QtCore.QSize(459, 612))
        MainWindow.setMaximumSize(QtCore.QSize(459, 583))
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
        self.install_btn.setGeometry(QtCore.QRect(313, 485, 131, 41))
        self.install_btn.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.install_btn.setObjectName("install_btn")
        self.pkgs_tableView = QtWidgets.QTableView(self.centralwidget)
        self.pkgs_tableView.setGeometry(QtCore.QRect(9, 129, 441, 261))
        self.pkgs_tableView.setObjectName("pkgs_tableView")
        self.load_label = QtWidgets.QLabel(self.centralwidget)
        self.load_label.setGeometry(QtCore.QRect(-60, 210, 571, 91))
        font = QtGui.QFont()
        font.setPointSize(50)
        self.load_label.setFont(font)
        self.load_label.setScaledContents(False)
        self.load_label.setAlignment(QtCore.Qt.AlignCenter)
        self.load_label.setObjectName("load_label")
        self.progress_bar = QtWidgets.QProgressBar(self.centralwidget)
        self.progress_bar.setEnabled(True)
        self.progress_bar.setGeometry(QtCore.QRect(13, 503, 288, 25))
        self.progress_bar.setProperty("value", 24)
        self.progress_bar.setObjectName("progress_bar")
        self.reconnectBtn = QtWidgets.QPushButton(self.centralwidget)
        self.reconnectBtn.setGeometry(QtCore.QRect(10, 466, 88, 27))
        self.reconnectBtn.setMinimumSize(QtCore.QSize(88, 27))
        self.reconnectBtn.setMaximumSize(QtCore.QSize(88, 27))
        self.reconnectBtn.setObjectName("reconnectBtn")
        self.progress_label = QtWidgets.QLabel(self.centralwidget)
        self.progress_label.setGeometry(QtCore.QRect(12, 533, 287, 19))
        self.progress_label.setText("")
        self.progress_label.setObjectName("progress_label")
        self.pkgs_tableView.raise_()
        self.team_label.raise_()
        self.team_combo.raise_()
        self.arch_label.raise_()
        self.arch_combo.raise_()
        self.ppa_label.raise_()
        self.ppa_combo.raise_()
        self.packages_label.raise_()
        self.kernelbuild_chk.raise_()
        self.lowlatency_chk.raise_()
        self.install_btn.raise_()
        self.load_label.raise_()
        self.progress_bar.raise_()
        self.reconnectBtn.raise_()
        self.progress_label.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.statusbar.sizePolicy().hasHeightForWidth())
        self.statusbar.setSizePolicy(sizePolicy)
        self.statusbar.setMinimumSize(QtCore.QSize(0, 0))
        self.statusbar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 459, 24))
        self.menuBar.setObjectName("menuBar")
        self.menuPreferences = QtWidgets.QMenu(self.menuBar)
        self.menuPreferences.setObjectName("menuPreferences")
        MainWindow.setMenuBar(self.menuBar)
        self.btn_edit_config = QtWidgets.QAction(MainWindow)
        self.btn_edit_config.setObjectName("btn_edit_config")
        self.btn_quit = QtWidgets.QAction(MainWindow)
        self.btn_quit.setObjectName("btn_quit")
        self.btn_refresh_cache = QtWidgets.QAction(MainWindow)
        self.btn_refresh_cache.setObjectName("btn_refresh_cache")
        self.menuPreferences.addAction(self.btn_refresh_cache)
        self.menuPreferences.addAction(self.btn_edit_config)
        self.menuPreferences.addSeparator()
        self.menuPreferences.addAction(self.btn_quit)
        self.menuBar.addAction(self.menuPreferences.menuAction())

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
        self.reconnectBtn.setText(_translate("MainWindow", "Reconnect"))
        self.menuPreferences.setTitle(_translate("MainWindow", "Preferences..."))
        self.btn_edit_config.setText(_translate("MainWindow", "Edit Configuration"))
        self.btn_quit.setText(_translate("MainWindow", "Exit"))
        self.btn_refresh_cache.setText(_translate("MainWindow", "Refresh Cache"))


