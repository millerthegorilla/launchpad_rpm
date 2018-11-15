# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources/ui/cadence_tb_jack.ui'
#
# Created: Tue Jul 11 07:46:42 2017
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(390, 118)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.rb_jack = QtGui.QRadioButton(Dialog)
        self.rb_jack.setChecked(True)
        self.rb_jack.setObjectName(_fromUtf8("rb_jack"))
        self.verticalLayout.addWidget(self.rb_jack)
        self.rb_ladish = QtGui.QRadioButton(Dialog)
        self.rb_ladish.setObjectName(_fromUtf8("rb_ladish"))
        self.verticalLayout.addWidget(self.rb_ladish)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(Dialog)
        self.label.setEnabled(False)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.cb_studio_name = QtGui.QComboBox(Dialog)
        self.cb_studio_name.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_studio_name.sizePolicy().hasHeightForWidth())
        self.cb_studio_name.setSizePolicy(sizePolicy)
        self.cb_studio_name.setObjectName(_fromUtf8("cb_studio_name"))
        self.horizontalLayout.addWidget(self.cb_studio_name)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QObject.connect(self.rb_ladish, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.label.setEnabled)
        QtCore.QObject.connect(self.rb_ladish, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cb_studio_name.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "JACK Options", None))
        self.rb_jack.setText(_translate("Dialog", "Load JACK Default Settings", None))
        self.rb_ladish.setText(_translate("Dialog", "Load LADISH Studio", None))
        self.label.setText(_translate("Dialog", "Studio Name:", None))

