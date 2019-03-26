#!/usr/bin/python3
import sys, requests, logging
import httplib2
from launchpadlib.errors import HTTPError
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QObject
from kxfed_ui import Ui_MainWindow
from kfconf import cfg, cache, pkg_states
import tvmodel
from kxfed_prefs import KxfedPrefsDialog
from kxfedmsgsdialog import KxfedMsgsDialog
import traceback


# TODO add installed packages to config
class MainW (QMainWindow, Ui_MainWindow):

    msg = pyqtSignal(str)
    log = pyqtSignal('PyQt_PyObject', int)
    progress_adjusted = pyqtSignal(int, int)
    transaction_progress_adjusted = pyqtSignal(int, int)
    lock_model_signal = pyqtSignal(bool)
    cancel_signal = pyqtSignal()

    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self._movie = QMovie("./assets/loader.gif")
        self.load_label.setMovie(self._movie)
        self.load_label.setMinimumWidth(200)
        self.load_label.setMinimumHeight(20)

        # preferences dialog
        self.kxfed_prefs_dialog = KxfedPrefsDialog()
        self.btn_edit_config.triggered.connect(self.show_prefs)

        # messages dialog
        self.kxfed_msgs_dialog = KxfedMsgsDialog()
        self.btn_show_messages.triggered.connect(self.show_msgs)
        self.pkgs_tableView.horizontalHeader().setStretchLastSection(True)
        self.pkgs_tableView.setStyleSheet("QTableView::QCheckBox::indicator { position : center; }")

        self._movie = QMovie("./assets/loader.gif")
        self.load_label.setMovie(self._movie)
        self.load_label.setMinimumWidth(200)
        self.load_label.setMinimumHeight(20)

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

        # preferences dialog
        self.kxfed_prefs_dialog = KxfedPrefsDialog()
        self.btn_edit_config.triggered.connect(self.show_prefs)

        # messages dialog
        self.kxfed_msgs_dialog = KxfedMsgsDialog()
        self.btn_show_messages.triggered.connect(self.show_msgs)

        self.kxfed = Kxfed(self)

        # connection button
        self.reconnectBtn.setVisible(False)
        self.reconnectBtn.pressed.connect(self.kxfed.connect)

        self.pkgs_tableView.setModel(self.kxfed.pkg_model)
        self.pkgs_tableView.horizontalHeader().setStretchLastSection(True)
        self.pkgs_tableView.setStyleSheet("QTableView::QCheckBox::indicator { position : center; }")

        # signals
        self.kxfed.pkg_model.list_filling.connect(self.toggle_pkg_list_loading)

        # self.main_window.pkg_model.message.connect(self.main_window.message_user, type=Qt.DirectConnection)
        self.msg.connect(self.message_user, type=Qt.DirectConnection)
        # self.main_window.pkg_model.packages.progress_adj.connect(self.main_window.progress_changed, type=Qt.DirectConnection)
        self.progress_adjusted.connect(self.progress_changed, type=Qt.DirectConnection)
        #
        # self.main_window.pkg_model.packages.log_msg.connect(self.main_window.log)
        self.log.connect(self.log_msg)
        # self.main_window.pkg_model.packages.cancelled.connect(self.main_window.cancelled)
        self.cancel_signal.connect(self.cancelled)
        # self.main_window.pkg_model.packages.transaction_progress_adjusted.connect(self.main_window.transaction_progress_changed)
        self.transaction_progress_adjusted.connect(self.transaction_progress_changed)
        #
        # self.main_window.pkg_model.packages.lock_model.connect(self.main_window.lock_model)
        self.lock_model_signal.connect(self.lock_model)

        self.ppa_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.arch_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.install_btn.clicked.connect(self.install_pkgs_button)

        self.install_btn.setText('Process Packages')

        self.progress_bar.setVisible(False)
        self.transaction_progress_bar.setVisible(False)

        # connection button
        self.reconnectBtn.setVisible(False)
        self.reconnectBtn.pressed.connect(self.kxfed.connect)

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

    def getboundmethod(self):
        return self.list_filling

    def refresh_cache(self):
        cache.invalidate(hard=True)
        self.kxfed.populate_pkgs()

    def show_prefs(self):
        self.kxfed_prefs_dialog.show()

    def show_msgs(self):
        self.kxfed_msgs_dialog.show()

    @pyqtSlot(bool)
    def lock_model(self, enabled):
        self.pkgs_tableView.setEnabled(enabled)

    @pyqtSlot()
    def cancelled(self):
        self.install_btn.setText('Process Packages')
        self.install_btn.clicked.connect(self.install_pkgs_button)

    @pyqtSlot()
    def toggle_pkg_list_loading(self):
        self.load_label.setVisible((not self.load_label.isVisible()))
        if self.load_label.isVisible():
            self._movie.start()
        else:
            self._movie.stop()
            self.pkgs_tableView.resizeColumnsToContents()
            self.pkgs_tableView.resizeRowsToContents()

    @pyqtSlot(int, int)
    def progress_changed(self, v, m):
        if m == 0 and v == 0:
            self.progress_bar.setVisible(False)
            self._download_total = 0
            self._download_current = 0
        else:
            if m != 0:
                self._download_total = m
            if v != 0:
                self._download_current += v
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self._download_total)
            self.progress_bar.setValue(self._download_current)
        QApplication.instance().processEvents()

    @pyqtSlot(int, int)
    def transaction_progress_changed(self, amount, total):
        if amount == 0 and total == 0:
            self.transaction_progress_bar.setVisible(False)
            self.transaction_progress_bar.setValue(0)
        else:
            self.transaction_progress_bar.setVisible(True)
            self.transaction_progress_bar.setMaximum(total)
            self.transaction_progress_bar.setValue(amount)

    @pyqtSlot(str)
    def message_user(self, msg):
        self.statusbar.showMessage(msg)

    @pyqtSlot('PyQt_PyObject', int)
    def log_msg(self, e, level=None):
        if level is None:
            level = logging.INFO
        if issubclass(type(e), Exception):
            tr = traceback.TracebackException.from_exception(e)
            log_record = logging.makeLogRecord({})
            log_record.name = tr.exc_type
            log_record.level = logging.ERROR
            if tr.stack:
                log_record.pathname = tr.stack[0].filename
                log_record.lineno = tr.stack[0].lineno
                log_record.args = tr.stack.format()
                log_record.func = tr.stack[len(tr.stack) - 1]
            else:
                log_record.pathname = None
                log_record.lineno = None
                log_record.args = None
                log_record.func = None
            log_record.msg = str(e)
            log_record.exc_info = tr.exc_type
            log_record.sinfo = tr.exc_traceback
            self.kxfed_msgs_dialog.log(log_record=log_record)
            self.message_user("Error.  See messages.")
        else:
            self.kxfed_msgs_dialog.log(msg=str(e), level=level)

    def populate_pkgs(self):
        try:
            self.kxfed.pkg_model.populate_pkg_list(
                self.ppa_combo.itemData(self.ppa_combo.currentIndex()),
                self.arch_combo.currentText())
        except Exception as e:
            self.log.emit(e, logging.ERROR)

    def install_pkgs_button(self):
        try:
            self.install_btn.setText('Cancel')
            self.install_btn.clicked.connect(self.cancel_process_button)
            self.kxfed.pkg_model.packages.install_pkgs_button()
        except Exception as e:
            self.log.emit(e, logging.ERROR)

    def cancel_process_button(self):
        self.kxfed.pkg_model.packages.cancel_process = True

    def closeEvent(self, event):
        """
        clean up :
            invalidate ie delete cache file if necessary
        :param event:
        :return:
        """
        result = QMessageBox.question(self,
                                      "Confirm Exit...",
                                      "Are you sure you want to exit ?",
                                      QMessageBox.Yes | QMessageBox.No)
        event.ignore()

        if result == QMessageBox.Yes:
            pkg_states['tobeinstalled'].clear()
            pkg_states['tobeuninstalled'].clear()
            try:
                cfg.filename = (cfg['config']['dir'] + cfg['config']['filename'])
                cfg.write()
            except OSError as e:
                self.log.emit(e, logging.CRITICAL)
            event.accept()


class Kxfed(QObject):

    msg = pyqtSignal(str)
    log = pyqtSignal('PyQt_PyObject', int)
    progress_adjusted = pyqtSignal(int, int)
    transaction_progress_adjusted = pyqtSignal(int, int)
    lock_model = pyqtSignal(bool)

    def __init__(self, mainw):
        super().__init__()
        self.main_window = mainw
        # instance variables
        self._ppas_json = {}
        self._team = "KXStudio-Debian"
        self.main_window.team_combo.addItem(self._team)
        self.main_window.arch_combo.addItem("amd64")
        self.main_window.arch_combo.addItem("i386")
        self.progress_adjusted.connect(mainw.progress_changed)
        self.transaction_progress_adjusted.connect(mainw.transaction_progress_changed)
        self.msg.connect(mainw.message_user)
        self.log.connect(mainw.log_msg)
        self.lock_model.connect(mainw.lock_model_signal)

        self.pkg_model = tvmodel.TVModel(['Installed', 'Pkg Name', 'Version', 'Description'],
                                         self.main_window.team_combo.currentText().lower(),
                                         self.main_window.arch_combo.currentText().lower(),
                                         self.progress_adjusted,
                                         self.transaction_progress_adjusted,
                                         self.msg,
                                         self.log,
                                         self.lock_model)

        self.main_window._download_total = 0
        self.main_window._download_current = 0

        # connect
        self.connect()

    @property
    def team(self):
        return self._team
    
    @property
    def pkg_model(self):
        return self._pkg_model

    @pkg_model.setter
    def pkg_model(self, pm):
        self._pkg_model = pm

    def connect(self):
        try:
            self._pkg_model.packages.connect()
            self.main_window.reconnectBtn.setVisible(False)
            self.populate_ppa_combo()
            self._pkg_model.populate_pkg_list(self.main_window.ppa_combo.currentData(),
                                              self.pkg_model.packages.arch)
            self.log.emit("Connected to Launchpad", logging.INFO)
        except (httplib2.ServerNotFoundError, HTTPError) as e:
            self.main_window.reconnectBtn.setVisible(True)
            self.log.emit(e, logging.ERROR)
            self.msg.emit('Error connecting - see messages for more detail - check your internet connection. ')

    def populate_ppa_combo(self):
        try:
            ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
            self.main_window._ppas_json = requests.get(ppas_link).json()
        except requests.HTTPError as e:
            self.log.emit(e, logging.CRITICAL)
        for ppa in self.main_window._ppas_json['entries']:
            self.main_window.ppa_combo.addItem(ppa['displayname'], ppa['name'])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = MainW()
    myapp.show()
    sys.exit(app.exec_())
