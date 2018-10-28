# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets

from treemodel import TreeModel
from packages import Packages

# import config, sys
# sys.path.append('/opt/settings')

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
        self.kernelbuild_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.kernelbuild_chk.setGeometry(QtCore.QRect(10, 400, 271, 21))
        self.kernelbuild_chk.setObjectName("kernelbuild_chk")
        self.lowlatency_chk = QtWidgets.QCheckBox(self.centralwidget)
        self.lowlatency_chk.setGeometry(QtCore.QRect(10, 420, 111, 21))
        self.lowlatency_chk.setObjectName("lowlatency_chk")
        self.packages_treeview = QtWidgets.QTreeView(self.centralwidget)
        self.packages_treeview.setGeometry(QtCore.QRect(10, 161, 431, 231))
        self.packages_treeview.setObjectName("packages_treeview")
        self.team_combo = QtWidgets.QComboBox(self.centralwidget)
        self.team_combo.setGeometry(QtCore.QRect(70, 10, 93, 26))
        self.team_combo.setObjectName("team_combo")
        self.team_combo.setEditable(True)
        self.team_combo.addItem("")
        self.team_label = QtWidgets.QLabel(self.centralwidget)
        self.team_label.setGeometry(QtCore.QRect(10, 10, 74, 18))
        self.team_label.setObjectName("team_label")
        self.ppa_label = QtWidgets.QLabel(self.centralwidget)
        self.ppa_label.setGeometry(QtCore.QRect(10, 100, 74, 18))
        self.ppa_label.setObjectName("ppa_label")
        self.ppa_combo = QtWidgets.QComboBox(self.centralwidget)
        self.ppa_combo.setEnabled(False)
        self.ppa_combo.setGeometry(QtCore.QRect(70, 100, 93, 26))
        self.ppa_combo.setObjectName("ppa_combo")
        self.packages_label = QtWidgets.QLabel(self.centralwidget)
        self.packages_label.setGeometry(QtCore.QRect(10, 140, 81, 18))
        self.packages_label.setObjectName("packages_label")
        self.arch_combo = QtWidgets.QComboBox(self.centralwidget)
        self.arch_combo.setGeometry(QtCore.QRect(70, 50, 93, 26))
        self.arch_combo.setObjectName("arch_combo")
        self.arch_combo.addItem("")
        self.arch_combo.addItem("")
        self.arch_label = QtWidgets.QLabel(self.centralwidget)
        self.arch_label.setGeometry(QtCore.QRect(10, 50, 74, 18))
        self.arch_label.setObjectName("arch_label")
        self.install_btn = QtWidgets.QPushButton(self.centralwidget)
        self.install_btn.setGeometry(QtCore.QRect(10, 450, 121, 41))
        self.install_btn.setObjectName("install_btn")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def setupModel(self):
        self._pkgmodel = TreeModel(['Installed', 'Pkg Name', 'Version', 'Description'], Packages(team, ppa, arch))

        self.packages_treeview.setModel(self._pkgmodel)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.kernelbuild_chk.setText(_translate("MainWindow", "Build and install latest RT kernel"))
        self.lowlatency_chk.setText(_translate("MainWindow", "Lowlatency"))
        self.team_combo.setItemText(0, _translate("MainWindow", "KxStudio-Debian"))
        self.team_label.setText(_translate("MainWindow", "Team :"))
        self.ppa_label.setText(_translate("MainWindow", "PPA :"))
        self.packages_label.setText(_translate("MainWindow", "Packages: "))
        self.arch_combo.setItemText(0, _translate("MainWindow", "AMD64"))
        self.arch_combo.setItemText(1, _translate("MainWindow", "X386"))
        self.arch_label.setText(_translate("MainWindow", "Arch :"))
        self.install_btn.setText(_translate("MainWindow", "Install"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

