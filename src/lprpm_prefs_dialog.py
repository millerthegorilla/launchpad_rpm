from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import Qt, pyqtSlot
from lprpm_conf import cfg, tmp_dir
from ui.lprpm_prefs_dialog_ui import UiLPRpmPrefsDialog
from datetime import datetime


class LPRpmPrefsDialog(QDialog):
    def __init__(self):
        super(LPRpmPrefsDialog, self).__init__()

        # Set up the user interface from Designer.
        self.ui = UiLPRpmPrefsDialog()
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
        self.ui.renew_every_time_chkbox.setCheckState(2 if cfg['initialised']['renew_period'] == "every_time" else 0)
        self.ui.renew_every_day_chkbox.setCheckState(2 if cfg['initialised']['renew_period'] == "daily" else 0)
        self.ui.renew_every_month_chkbox.setCheckState(2 if cfg['initialised']['renew_period'] == "monthly" else 0)
        self.ui.renew_every_6_months_chkbox.setCheckState(2 if cfg['initialised']['renew_period'] == "6months" else 0)
        # signals
        self.ui.directory_label.clicked.connect(self.openFileNameDialog)
        self.ui.download_chkbox.stateChanged.connect(self.download_checkbox_changed)
        self.ui.convert_chkbox.stateChanged.connect(self.convert_checkbox_changed)
        self.ui.install_chkbox.stateChanged.connect(self.install_checkbox_changed)
        self.ui.uninstall_chkbox.stateChanged.connect(self.uninstall_checkbox_changed)
        self.ui.delete_converted_chkbox.stateChanged.connect(self.delete_converted_changed)
        self.ui.delete_downloaded_chkbox.stateChanged.connect(self.delete_downloaded_changed)
        self.ui.closeButton.clicked.connect(self._close)
        self.ui.renew_every_time_chkbox.clicked.connect(self.renew_cache_every_time_clicked)
        self.ui.renew_every_month_chkbox.clicked.connect(self.renew_cache_monthly_clicked)
        self.ui.renew_every_6_months_chkbox.clicked.connect(self.renew_cache_6months_clicked)
        self.ui.renew_every_day_chkbox.clicked.connect(self.renew_cache_daily_clicked)
        self.day = datetime.now().date().day
        self.month = datetime.now().date().month
        self.year = datetime.now().date().year

    def _close(self):
        self.hide()

    @pyqtSlot()
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

    @pyqtSlot()
    def download_checkbox_changed(self):
        cfg['download'] = str(self.ui.download_chkbox.isChecked())

    @pyqtSlot()
    def convert_checkbox_changed(self):
        cfg['convert'] = str(self.ui.convert_chkbox.isChecked())

    @pyqtSlot()
    def install_checkbox_changed(self):
        cfg['install'] = str(self.ui.install_chkbox.isChecked())

    @pyqtSlot()
    def uninstall_checkbox_changed(self):
        cfg['uninstall'] = str(self.ui.uninstall_chkbox.isChecked())

    @pyqtSlot()
    def delete_converted_changed(self):
        cfg['delete_converted'] = str(self.ui.delete_converted_chkbox.isChecked())

    @pyqtSlot()
    def delete_downloaded_changed(self):
        cfg['delete_downloaded'] = str(self.ui.delete_downloaded_chkbox.isChecked())

    @pyqtSlot()
    def renew_cache_daily_clicked(self):
        self.ui.renew_every_6_months_chkbox.setChecked(False)
        self.ui.renew_every_month_chkbox.setChecked(False)
        self.ui.renew_every_time_chkbox.setChecked(False)
        cfg['initialised']['renew_period'] = "daily"
        cfg['initialised']['day'] = self.day
        cfg['initialised']['month'] = self.month
        cfg['initialised']['year'] = self.year

    @pyqtSlot()
    def renew_cache_monthly_clicked(self):
        self.ui.renew_every_6_months_chkbox.setCheckState(Qt.Unchecked)
        self.ui.renew_every_day_chkbox.setCheckState(Qt.Unchecked)
        self.ui.renew_every_time_chkbox.setCheckState(Qt.Unchecked)
        cfg['initialised']['renew_period'] = "monthly"
        cfg['initialised']['day'] = self.day
        cfg['initialised']['month'] = self.month
        cfg['initialised']['year'] = self.year

    @pyqtSlot()
    def renew_cache_6months_clicked(self):
        self.ui.renew_every_day_chkbox.setCheckState(Qt.Unchecked)
        self.ui.renew_every_month_chkbox.setCheckState(Qt.Unchecked)
        self.ui.renew_every_time_chkbox.setCheckState(Qt.Unchecked)
        cfg['initialised']['renew_period'] = "6months"
        cfg['initialised']['day'] = self.day
        cfg['initialised']['month'] = self.month
        cfg['initialised']['year'] = self.year

    @pyqtSlot()
    def renew_cache_every_time_clicked(self):
        self.ui.renew_every_6_months_chkbox.setCheckState(Qt.Unchecked)
        self.ui.renew_every_month_chkbox.setCheckState(Qt.Unchecked)
        self.ui.renew_every_day_chkbox.setCheckState(Qt.Unchecked)
        cfg['initialised']['renew_period'] = "every_time"

