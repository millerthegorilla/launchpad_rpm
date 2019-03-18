#!/usr/bin/python3
import sys, requests, logging, traceback
import httplib2
from launchpadlib.errors import HTTPError
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import Qt
from kxfed_ui import Ui_MainWindow
import kfconf
from tvmodel import TVModel
from kxfed_prefs import KxfedPrefsDialog
from kxfedmsgsdialog import KxfedMsgsDialog
import traceback


# TODO add installed packages to config
# TODO after installing them, using rpm from bookmarked website rpm library
class MainW (QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        # instance variables
        self._ppas_json = {}
        self.team = "KXStudio-Debian"

        # config variables
        self.team_combo.addItem(self.team)
        self.arch_combo.addItem("amd64")
        self.arch_combo.addItem("i386")
        self.pkg_model = TVModel(['Installed', 'Pkg Name', 'Version', 'Description'],
                                 self.team_combo.currentText().lower(),
                                 self.arch_combo.currentText().lower())
        self.pkgs_tableView.setModel(self.pkg_model)
        self.pkgs_tableView.horizontalHeader().setStretchLastSection(True)
        self.pkgs_tableView.setStyleSheet("QTableView::QCheckBox::indicator { position : center; }")

        # status bar
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.statusbar.addWidget(self.label)

        # connection button
        self.reconnectBtn.setVisible(False)
        self.reconnectBtn.pressed.connect(self.connect)

        self._movie = QMovie("./assets/loader.gif")
        self.load_label.setMovie(self._movie)
        self.load_label.setMinimumWidth(200)
        self.load_label.setMinimumHeight(20)

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

        # preferences dialog
        self.kxfed_prefs_dialog = KxfedPrefsDialog()
        self.btn_edit_config.triggered.connect(self.show_prefs)

        # messages
        self.kxfed_msgs_dialog = KxfedMsgsDialog()
        self.btn_show_messages.triggered.connect(self.show_msgs)

        # signals
        self.pkg_model.list_filled.connect(self.toggle_pkg_list_loading)
        self.pkg_model.message.connect(self.message_user, type=Qt.DirectConnection)
        self.pkg_model.packages.progress_adjusted.connect(self.progress_changed, type=Qt.DirectConnection)
        self.pkg_model.packages.message.connect(self.message_user)
        self.pkg_model.packages.log.connect(self.log)

        # user signals
        self.ppa_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.arch_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.install_btn.clicked.connect(self.install_pkgs_button)

        self.progress_bar.setVisible(False)
        self._download_total = 0
        self._download_current = 0

        # connect
        self.connect()

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
            kfconf.cfg['tobeinstalled'].clear()
            kfconf.cfg['tobeuninstalled'].clear()
            try:
                kfconf.cfg.filename = (kfconf.cfg['config']['dir'] + kfconf.cfg['config']['filename'])
                kfconf.cfg.write()
            except OSError as e:
                self.log(e)
            event.accept()

    def connect(self):
        try:
            self.pkg_model.packages.connect()
            self.reconnectBtn.setVisible(False)
            self.populate_ppa_combo()
            self.pkg_model.list_filled.emit()
            self.log("Connected to Launchpad")
        except (httplib2.ServerNotFoundError, HTTPError) as e:
            self.reconnectBtn.setVisible(True)
            self.log(e)
            self.message_user('Error connecting - see messages for more detail - check your internet connection. ')

    def populate_ppa_combo(self):
        try:
            ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
            self._ppas_json = requests.get(ppas_link).json()
        except requests.HTTPError as e:
            self.log(e)
        for ppa in self._ppas_json['entries']:
            self.ppa_combo.addItem(ppa['displayname'], ppa['name'])

    def install_pkgs_button(self):
        try:
            self.pkg_model.packages.install_pkgs_button()
        except Exception as e:
            self.log(e)

    def populate_pkgs(self):
        try:
            self.pkg_model.populate_pkg_list(self.ppa_combo.itemData(self.ppa_combo.currentIndex()),
                                             self.arch_combo.currentText())
        except Exception as e:
            self.log(e)

    @pyqtSlot()
    def toggle_pkg_list_loading(self):
        self.load_label.setVisible((not self.load_label.isVisible()))
        if self.load_label.isVisible():
            self._movie.start()
        else:
            self._movie.stop()
            self.pkgs_tableView.resizeColumnsToContents()

    @pyqtSlot(int, int)
    def progress_changed(self, v, m):
        if m == 0 and v == 0:
            self.progress_bar.setVisible(False)
            self._download_total = 0
            self._download_current = 0
        else:
            if m != 0:
                self._download_total += m
            if v != 0:
                self._download_current += v
            self.statusbar.showMessage("Downloading Packages")
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self._download_total)
            self.progress_bar.setValue(self._download_current)

    @pyqtSlot(str)
    def message_user(self, msg):
        self.label.setText(msg)

    def hide_message(self, ev):
        self.label.setText('')

    def refresh_cache(self):
        kfconf.cache.invalidate(hard=True)
        self.populate_pkgs()

    def show_prefs(self):
        self.kxfed_prefs_dialog.show()

    def show_msgs(self):
        self.kxfed_msgs_dialog.show()

    @pyqtSlot('PyQt_PyObject')
    def log(self, e):
        if issubclass(type(e), Exception):
            tr = traceback.TracebackException.from_exception(e)
            log_record = logging.makeLogRecord({})
            log_record.name = tr.exc_type
            log_record.level = logging.ERROR
            log_record.pathname = tr.stack[0].filename
            log_record.lineno = tr.stack[0].lineno
            log_record.msg = str(e)
            log_record.args = tr.stack.format()
            log_record.exc_info = tr.exc_type
            log_record.func = tr.stack[len(tr.stack) - 1]
            log_record.sinfo = tr.exc_traceback
            self.kxfed_msgs_dialog.log(log_record=log_record)
            self.message_user("Error.  See messages.")
        else:
            self.kxfed_msgs_dialog.log(msg=str(e))
            self.message_user(str(e) + " See messages")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = MainW()
    myapp.show()
    sys.exit(app.exec_())
