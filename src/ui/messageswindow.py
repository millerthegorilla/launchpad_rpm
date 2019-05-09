from PyQt5.QtWidgets import QPlainTextEdit


class MessagesWindow(QPlainTextEdit):
    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)

    def appendPlainText(self, p_str):
        super().appendPlainText(p_str)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
