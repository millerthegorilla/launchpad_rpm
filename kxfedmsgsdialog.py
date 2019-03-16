from PyQt5.QtWidgets import QDialog
from kxfedmsgsdialog_ui import Ui_KxfedMsgsDialog
from messageswindow import MessagesWindow


# TODO - add and sort out logging in MessagesWindow
class KxfedMsgsDialog(QDialog):
    def __init__(self):
        super(KxfedMsgsDialog, self).__init__()
        self.ui = Ui_KxfedMsgsDialog()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.close)
