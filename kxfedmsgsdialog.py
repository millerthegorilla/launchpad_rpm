import logging
import logging.handlers

from PyQt5.QtWidgets import QDialog
import dnf

from kfconf import cfg
from kxfedmsgsdialog_ui import Ui_KxfedMsgsDialog


# TODO - add and sort out logging in MessagesWindow
class KxfedMsgsDialog(QDialog):
    def __init__(self):
        super(KxfedMsgsDialog, self).__init__()
        self.ui = Ui_KxfedMsgsDialog()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.close)
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False
        handler = logging.handlers.RotatingFileHandler(
            cfg["log_file_path"], maxBytes=50000, backupCount=5)
        format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(format)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.addHandler(dnf.base.logger)

    def log(self, log_record=None, msg=None, level=None):
        log_msg = ""
        if level is None:
            level = logging.INFO
        if log_record:
            if log_record.name:
                log_msg = "name : " + str(log_record.name) + " \n "
            if log_record.level:
                log_msg += "level : " + str(logging.getLevelName(log_record.level)) + " \n "
            if log_record.pathname:
                log_msg += "module : " + str(log_record.pathname) + " \n "
            if log_record.lineno:
                log_msg += "line no : " + str(log_record.lineno) + " \n "
            if log_record.msg:
                log_msg += "message : " + str(log_record.msg) + " \n "
            if log_record.args:
                log_msg += "args : " + str(log_record.args) + " \n "
            if log_record.exc_info:
                log_msg += "exc_info : " + str(log_record.exc_info) + " \n "
            if log_record.func:
                log_msg += "function : " + str(log_record.func) + " \n "
            if log_record.sinfo:
                log_msg += "stack info : " + str(log_record.sinfo)
            level = log_record.level | logging.INFO
        elif msg:
            log_msg = msg
            if not level:
                level = logging.INFO

        if log_msg != "":
            self.ui.plainTextEdit.appendPlainText(log_msg)
            self.logger.log(level=level, msg=log_msg)
        else:
            self.ui.plainTextEdit.appendPlainText("log function called without info")
            self.logger.log(level=level, msg="no message")
