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
        MainWindow.resize(475, 629)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(459, 629))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.lowlatency_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.lowlatency_chk.setObjectName("lowlatency_chk")
        self.gridLayout.addWidget(self.lowlatency_chk, 7, 0, 1, 1)
        self.reconnectBtn = QtWidgets.QPushButton(self.centralwidget)
        self.reconnectBtn.setMinimumSize(QtCore.QSize(88, 27))
        self.reconnectBtn.setMaximumSize(QtCore.QSize(88, 27))
        self.reconnectBtn.setObjectName("reconnectBtn")
        self.gridLayout.addWidget(self.reconnectBtn, 8, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.team_label = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.team_label.sizePolicy().hasHeightForWidth())
        self.team_label.setSizePolicy(sizePolicy)
        self.team_label.setObjectName("team_label")
        self.horizontalLayout_2.addWidget(self.team_label)
        self.team_combo = QtWidgets.QComboBox(self.centralwidget)
        self.team_combo.setEnabled(False)
        self.team_combo.setEditable(False)
        self.team_combo.setObjectName("team_combo")
        self.horizontalLayout_2.addWidget(self.team_combo)
        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 9)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.install_btn = QtWidgets.QPushButton(self.centralwidget)
        self.install_btn.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.install_btn.setObjectName("install_btn")
        self.horizontalLayout_4.addWidget(self.install_btn)
        self.gridLayout.addLayout(self.horizontalLayout_4, 10, 0, 1, 1)
        self.progress_bar = QtWidgets.QProgressBar(self.centralwidget)
        self.progress_bar.setEnabled(True)
        self.progress_bar.setProperty("value", 24)
        self.progress_bar.setObjectName("progress_bar")
        self.gridLayout.addWidget(self.progress_bar, 9, 0, 1, 1)
        self.packages_label = QtWidgets.QLabel(self.centralwidget)
        self.packages_label.setObjectName("packages_label")
        self.gridLayout.addWidget(self.packages_label, 4, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.arch_label = QtWidgets.QLabel(self.centralwidget)
        self.arch_label.setObjectName("arch_label")
        self.horizontalLayout.addWidget(self.arch_label)
        self.arch_combo = QtWidgets.QComboBox(self.centralwidget)
        self.arch_combo.setObjectName("arch_combo")
        self.horizontalLayout.addWidget(self.arch_combo)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 9)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.kernelbuild_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.kernelbuild_chk.setObjectName("kernelbuild_chk")
        self.gridLayout.addWidget(self.kernelbuild_chk, 6, 0, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.ppa_label = QtWidgets.QLabel(self.centralwidget)
        self.ppa_label.setObjectName("ppa_label")
        self.horizontalLayout_3.addWidget(self.ppa_label)
        self.ppa_combo = QtWidgets.QComboBox(self.centralwidget)
        self.ppa_combo.setEnabled(True)
        self.ppa_combo.setObjectName("ppa_combo")
        self.horizontalLayout_3.addWidget(self.ppa_combo)
        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 9)
        self.gridLayout.addLayout(self.horizontalLayout_3, 2, 0, 1, 1)
        self.pkgs_tableView = QtWidgets.QTableView(self.centralwidget)
        self.pkgs_tableView.setObjectName("pkgs_tableView")
        self.gridLayout.addWidget(self.pkgs_tableView, 3, 0, 1, 1)
        self.load_label = QtWidgets.QLabel(self.centralwidget)
        self.load_label.setGeometry(QtCore.QRect(134, 287, 67, 19))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.load_label.sizePolicy().hasHeightForWidth())
        self.load_label.setSizePolicy(sizePolicy)
        self.load_label.setAlignment(QtCore.Qt.AlignCenter)
        self.load_label.setObjectName("load_label")
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
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 475, 27))
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
        self.btn_show_messages = QtWidgets.QAction(MainWindow)
        self.btn_show_messages.setObjectName("btn_show_messages")
        self.menuPreferences.addAction(self.btn_refresh_cache)
        self.menuPreferences.addAction(self.btn_show_messages)
        self.menuPreferences.addAction(self.btn_edit_config)
        self.menuPreferences.addSeparator()
        self.menuPreferences.addAction(self.btn_quit)
        self.menuBar.addAction(self.menuPreferences.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "KXFed - KXStudio on Fedora"))
        self.lowlatency_chk.setText(_translate("MainWindow", "Lowlatency"))
        self.reconnectBtn.setText(_translate("MainWindow", "Reconnect"))
        self.team_label.setText(_translate("MainWindow", "Team :"))
        self.install_btn.setText(_translate("MainWindow", "Install"))
        self.packages_label.setText(_translate("MainWindow", "Packages: "))
        self.arch_label.setText(_translate("MainWindow", "Arch :"))
        self.kernelbuild_chk.setText(_translate("MainWindow", "Build and install latest RT kernel"))
        self.ppa_label.setText(_translate("MainWindow", "PPA :"))
        self.load_label.setText(_translate("MainWindow", "TextLabel"))
        self.menuPreferences.setTitle(_translate("MainWindow", "&Preferences..."))
        self.btn_edit_config.setText(_translate("MainWindow", "&Edit Configuration"))
        self.btn_quit.setText(_translate("MainWindow", "Exit"))
        self.btn_refresh_cache.setText(_translate("MainWindow", "&Refresh Cache"))
        self.btn_show_messages.setText(_translate("MainWindow", "&Messages"))


