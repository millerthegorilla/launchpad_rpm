from PyQt5.QtWidgets import QDialog
from kxfedmsgsdialog_ui import Ui_KxfedMsgsDialog
import logging
import logging.handlers
from kfconf import cfg


# TODO - add and sort out logging in MessagesWindow
class KxfedMsgsDialog(QDialog):
    def __init__(self):
        super(KxfedMsgsDialog, self).__init__()
        self.ui = Ui_KxfedMsgsDialog()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.close)
        self.logger = logging.getLogger(__name__)
        handler = logging.handlers.RotatingFileHandler(
            cfg["log_file_path"], maxBytes=2000, backupCount=5)
        format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(format)
        self.logger.addHandler(handler)

    def log(self, log_record=None, msg=None):
        log_msg = ""
        level = logging.INFO
        if log_record:
            if log_record.name:
                log_msg = "name : " + log_record.name + " : "
            if log_record.level:
                log_msg += "level : " + log_record.level + " : "
            if log_record.pathname:
                log_msg += "module : " + log_record.pathname + " : "
            if log_record.lineno:
                log_msg += "line no : " + log_record.lineno + " : "
            if log_record.msg:
                log_msg += "message : " + log_record.msg + " : "
            if log_record.args:
                log_msg += "args : " + log_record.args + " : "
            if log_record.exc_info:
                log_msg += "exc_info : " + log_record.exc_info + " : "
            if log_record.func:
                log_msg += "function : " + log_record.func + " : "
            if log_record.sinfo:
                log_msg += "stack info : " + log_record.sinfo
            level = log_record.level | logging.INFO
        elif msg:
            log_msg = msg
            level = logging.INFO

        if log_msg != "":
            self.ui.plainTextEdit.appendPlainText(log_msg)
            self.logger.log(level=level, msg=log_msg)
        else:
            self.ui.plainTextEdit.appendPlainText("log function called without info")
            self.logger.log(level=logging.INFO, msg="no message")

