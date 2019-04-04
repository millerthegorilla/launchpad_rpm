from PyQt5.QtWidgets import QDialog, QFileDialog

import kfconf
from kxfed_prefs_ui import Ui_prefs_dialog


class KxfedPrefsDialog(QDialog):
    def __init__(self):
        super(KxfedPrefsDialog, self).__init__()

        # Set up the user interface from Designer.
        self.ui = Ui_prefs_dialog()
        self.ui.setupUi(self)
        self.ui.directory_label.setToolTip(
            "The directories that store the deb and rpm files are located here, as well as the temporary conversion files")
        self.ui.directory_label.setText(kfconf.tmp_dir)
        self.ui.directory_label.clicked.connect(self.openFileNameDialog)
        self.ui.download_chkbox.stateChanged.connect(self.download_checkbox_changed)
        self.ui.convert_chkbox.stateChanged.connect(self.convert_checkbox_changed)
        self.ui.install_chkbox.stateChanged.connect(self.install_checkbox_changed)
        self.ui.delete_convert_chkbox.stateChanged.connect(self.delete_converted_changed)
        self.ui.delete_downloaded_chkbox.stateChanged.connect(self.delete_downloaded_changed)

    def accept(self):
        self.hide()

    def reject(self):
        self.hide()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename = str(QFileDialog.getExistingDirectory(self, "Select Directory", options=options))
        # fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
        #                                           "All Files (*);;Python Files (*.py)", options=options)
        if filename != '':
            self.ui.directory_label.setText(filename)
            kfconf.tmp_dir = filename
            kfconf.set_dirs()
        else:
            self.ui.directory_label.setText(kfconf.tmp_dir)

    def download_checkbox_changed(self):
        kfconf.cfg['download'] = str(self.ui.download_chkbox.isChecked())

    def convert_checkbox_changed(self):
        kfconf.cfg['convert'] = str(self.ui.convert_chkbox.isChecked())

    def install_checkbox_changed(self):
        kfconf.cfg['install'] = str(self.ui.install_chkbox.isChecked())

    def delete_converted_changed(self):
        kfconf.cfg['delete_converted'] = str(self.ui.delete_convert_chkbox.isChecked())

    def delete_downloaded_changed(self):
        kfconf.cfg['delete_downloaded'] = str(self.ui.delete_downloaded_chkbox.isChecked())
