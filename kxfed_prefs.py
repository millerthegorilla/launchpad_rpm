from PyQt5.QtWidgets import QDialog
from kxfed_prefs_ui import Ui_prefs_dialog
from PyQt5.QtWidgets import QFileDialog
import kfconf


class KxfedPrefsDialog(QDialog):
    def __init__(self):
        super(KxfedPrefsDialog, self).__init__()

        # Set up the user interface from Designer.
        self.ui = Ui_prefs_dialog()
        self.ui.setupUi(self)
        self.ui.directory_label.setText(kfconf.tmp_dir)
        self.ui.directory_label.clicked.connect(self.openFileNameDialog)

    def accept(self):
        pass

    def reject(self):
        self.hide()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename = str(QFileDialog.getExistingDirectory(self, "Select Directory", options=options))
        # fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
        #                                           "All Files (*);;Python Files (*.py)", options=options)
        if filename is not None:
            self.ui.directory_label.setText(filename)
            kfconf.tmp_dir = filename
            kfconf.set_dirs()
        else:
            self.ui.directory_label.setText(kfconf.tmp_dir)
