# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'kxfed.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QListWidgetItem
# import threading, subprocess
# from typing import Union


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.centralWidget = QtWidgets.QWidget(self)
        self.listWidget = QtWidgets.QListWidget(self.centralWidget)
        self.pushButton = QtWidgets.QPushButton(self.centralWidget)
        self.statusBar = QtWidgets.QStatusBar(self)

    def setup(self):
        self.setObjectName("MainWindow")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.resize(383, 324)
        sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizepolicy.setHorizontalStretch(0)
        sizepolicy.setVerticalStretch(0)
        sizepolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizepolicy)
        self.centralWidget.setObjectName("centralwidget")
        self.listWidget.setGeometry(QtCore.QRect(60, 40, 256, 192))
        self.listWidget.setObjectName("listWidget")
        self.pushButton.setGeometry(QtCore.QRect(60, 250, 121, 41))
        self.pushButton.setObjectName("pushButton")
        self.setCentralWidget(self.centralWidget)
        self.statusBar.setObjectName("statusbar")
        self.setStatusBar(self.statusBar)

        self.translate()
        QtCore.QMetaObject.connectSlotsByName(self)
        item: QListWidgetItem = QtWidgets.QListWidgetItem()
        item.setText(QtCore.QCoreApplication.translate("Href_Gui", "Text:"))
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Unchecked)
        self.listWidget.addItem(item)

    def translate(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "Install"))

    def log(self, msg='', level='info',
            exception=None, std_out=False, to_disk=False):
        log_level = {
            'debug'     : logging.debug,
            'info'      : logging.info,
            'warning'   : logging.warning,
            'error'     : logging.error,
            'critical'  : logging.critical
        }.get(level, logging.debug('unable to log - check syntax'))
        if exception is not None:
            raise type(exception)(msg)
        if std_out is not False:
            log_level(msg)

    # class FuncThread(threading.Thread):
    #     def __init__(self, target, *args):
    #         self._target = target
    #         self._args = args
    #         threading.Thread.__init__(self)
    #
    #     def run(self):
    #         self._target(*self._args)


    # def runprocess(self, exe):
    #     p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     returncode = p.poll() # returns None while subprocess is running
    #     while returncode is not None:
    #         line: Union[str, bytes] = p.stdout.readlilsne()
    #         yield line


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.setup()
    ui.show()
    sys.exit(app.exec_())

