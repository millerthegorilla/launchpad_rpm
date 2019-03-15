#!/usr/bin/python3
import sys, requests, logging, traceback
import httplib2
from launchpadlib.errors import HTTPError
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import pyqtSlot
import PyQt5.QtCore
from kxfed_ui import Ui_MainWindow
import kfconf
from tvmodel import TVModel
from kxfed_prefs import KxfedPrefsDialog


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
        self.arch_combo.addItem("x86")
        self.pkg_model = TVModel(['Installed', 'Pkg Name', 'Version', 'Description'],
                                 self.team_combo.currentText().lower(),
                                 self.arch_combo.currentText().lower())
        self.pkgs_tableView.setModel(self.pkg_model)
        self.pkgs_tableView.horizontalHeader().setStretchLastSection(True)
        self.pkgs_tableView.setStyleSheet("QTableView::QCheckBox::indicator { position : center; }")

        # status bar
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.timerEvent = self.hide_message
        self.statusbar.addWidget(self.label)

        # connection button
        self.reconnectBtn.setVisible(False)
        self.reconnectBtn.pressed.connect(self.connect)

        self._movie = QMovie("./assets/loader.gif")

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

        # preferences dialog
        self.kxfed_prefs_dialog = KxfedPrefsDialog()
        self.btn_edit_config.triggered.connect(self.show_prefs)

        # signals
        self.pkg_model.list_filled.connect(self.toggle_pkg_list_loading)
        self.pkg_model.message.connect(self.message_user, type=PyQt5.QtCore.Qt.DirectConnection)
        self.pkg_model.packages.progress_adjusted.connect(self.progress_changed, type=PyQt5.QtCore.Qt.DirectConnection)
        self.pkg_model.packages.progress_label.connect(self.progress_label_change)
        self.pkg_model.packages.message.connect(self.message_user)
        self.pkg_model.packages.exception.connect(self._exception)

        # user signals
        self.ppa_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.install_btn.clicked.connect(self.install_pkgs_button)

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
                logging.log(logging.CRITICAL, str(e) + "\n" + traceback.format_exc())
            event.accept()

    def showEvent(self, ev):
        # progress label
        self.load_label.setMovie(self._movie)
        self._movie.start()
        self.load_label.setVisible(True)

        # progress bar
        self.progress_bar.setVisible(False)
        self._download_total = 0
        self._download_current = 0
        return QWidget.showEvent(self, ev)

    def connect(self):
        try:
            self.pkg_model.packages.connect()
            self.reconnectBtn.setVisible(False)
            self.populate_ppa_combo()
            self.pkg_model.list_filled.emit()
            self.message_user('Connected to Launchpad')
        except (httplib2.ServerNotFoundError, HTTPError) as e:
            self.reconnectBtn.setVisible(True)
            self.message_user(str(e) + ' - perhaps check your internet connection. ')

    def populate_ppa_combo(self):
        try:
            ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
            self._ppas_json = requests.get(ppas_link).json()
        except requests.HTTPError as e:
            logging.log("error", e.strerror)
            self.message_user(e.strerror)
        for ppa in self._ppas_json['entries']:
            self.ppa_combo.addItem(ppa['displayname'], ppa['name'])

    def install_pkgs_button(self):
        try:
            self.pkg_model.packages.install_pkgs_button()
            # TODO do not show the above message again option
        except Exception as e:
            logging.log(logging.CRITICAL, str(e) + "\n" + traceback.format_exc())
            self.message_user('Critical Error, Exiting')

    def populate_pkgs(self):
        try:
            self.pkg_model.populate_pkg_list(self.ppa_combo.itemData(self.ppa_combo.currentIndex()))
        except Exception as e:
            logging.log(logging.ERROR, str(e))
            self.message_user(traceback.format_exc())

    @pyqtSlot()
    def toggle_pkg_list_loading(self):
        self.load_label.setVisible((not self.load_label.isVisible()))
        if self.load_label.isVisible():
            self._movie.start()
        else:
            self._movie.stop()
            self.pkgs_tableView.resizeColumnsToContents()


    # def toggle_pkg_list_loading(self, visible):
    #     if visible is True:
    #         self.load_label.setVisible(True)
    #         self.__movie.start()
    #     else:
    #         self.__movie.stop()
    #         self.load_label.setVisible(False)
    #     self.pkgs_tableView.resizeColumnsToContents()

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
    def progress_label_change(self, s):
        self.progress_label.setText(s)

    @pyqtSlot(str)
    def message_user(self, msg):   # , timeout=0, exit=False):
        self.label.setText(msg)
        # if timeout:
        #     self.label.startTimer(timeout)
        #     self._exit = exit

    def hide_message(self, ev):
        self.label.setText('')
        if self._exit:
            exit(1)

    @pyqtSlot('PyQt_PyObject')
    def _exception(self, ex):
        self.message_user(str(ex))
        raise type(ex)(traceback.format_exc())

    @staticmethod
    def refresh_cache(self):
        kfconf.cache.invalidate(hard=True)

    def show_prefs(self):
        self.kxfed_prefs_dialog.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = MainW()
    myapp.show()
    sys.exit(app.exec_())
