from PyQt5.QtWidgets import QDialog, QFileDialog
from lprpm_conf import cfg, tmp_dir
from ui.lprpm_prefs_ui import UiPrefsDialog


class LPRpmPrefsDialog(QDialog):
    def __init__(self):
        super(LPRpmPrefsDialog, self).__init__()

        # Set up the user interface from Designer.
        self.ui = UiPrefsDialog()
        self.ui.setupUi(self)
        self.ui.directory_label.setToolTip(
            "The directories that store the deb and rpm files are located here, \
            as well as the temporary conversion files and the log files.  Click to change...")
        self.ui.directory_label.setText(tmp_dir)
        self.ui.download_chkbox.setTristate(False)
        self.ui.convert_chkbox.setTristate(False)
        self.ui.install_chkbox.setTristate(False)
        self.ui.uninstall_chkbox.setTristate(False)
        self.ui.delete_downloaded_chkbox.setTristate(False)
        self.ui.delete_converted_chkbox.setTristate(False)
        self.ui.download_chkbox.setCheckState(2 if cfg.as_bool('download') else 0)
        self.ui.convert_chkbox.setCheckState(2 if cfg.as_bool('convert') else 0)
        self.ui.install_chkbox.setCheckState(2 if cfg.as_bool('install') else 0)
        self.ui.uninstall_chkbox.setCheckState(2 if cfg.as_bool('uninstall') else 0)
        self.ui.delete_downloaded_chkbox.setCheckState(2 if cfg.as_bool('delete_downloaded') else 0)
        self.ui.delete_converted_chkbox.setCheckState(2 if cfg.as_bool('delete_converted') else 0)
        # signals
        self.ui.directory_label.clicked.connect(self.openFileNameDialog)
        self.ui.download_chkbox.stateChanged.connect(self.download_checkbox_changed)
        self.ui.convert_chkbox.stateChanged.connect(self.convert_checkbox_changed)
        self.ui.install_chkbox.stateChanged.connect(self.install_checkbox_changed)
        self.ui.uninstall_chkbox.stateChanged.connect(self.uninstall_checkbox_changed)
        self.ui.delete_converted_chkbox.stateChanged.connect(self.delete_converted_changed)
        self.ui.delete_downloaded_chkbox.stateChanged.connect(self.delete_downloaded_changed)

    def accept(self):
        self.hide()

    def reject(self):
        self.hide()

    def openFileNameDialog(self):
        global tmp_dir
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename = str(QFileDialog.getExistingDirectory(self, "Select Directory", options=options))
        # fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
        #                                           "All Files (*);;Python Files (*.py)", options=options)
        if filename != '':
            self.ui.directory_label.setText(filename)
            tmp_dir = filename
        else:
            self.ui.directory_label.setText(tmp_dir)

    def download_checkbox_changed(self):
        cfg['download'] = str(self.ui.download_chkbox.isChecked())

    def convert_checkbox_changed(self):
        cfg['convert'] = str(self.ui.convert_chkbox.isChecked())

    def install_checkbox_changed(self):
        cfg['install'] = str(self.ui.install_chkbox.isChecked())

    def uninstall_checkbox_changed(self):
        cfg['uninstall'] = str(self.ui.uninstall_chkbox.isChecked())

    def delete_converted_changed(self):
        cfg['delete_converted'] = str(self.ui.delete_convert_chkbox.isChecked())

    def delete_downloaded_changed(self):
        cfg['delete_downloaded'] = str(self.ui.delete_downloaded_chkbox.isChecked())
