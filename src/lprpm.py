#!/usr/bin/python3
import logging
import sys

import httplib2
import requests
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import QApplication
from launchpadlib.errors import HTTPError

from treeview.pkg_tvmodel import PkgTVModel
from lprpm_conf import cfg, initialize_search, \
                        clean_installed, ENDED_ERR, ENDED_CANCEL, \
                        ENDED_SUCC, ENDED_NTD
import lprpm_main_window


class LPRpm(QThread):
    msg_signal = pyqtSignal(str)
    log_signal = pyqtSignal('PyQt_PyObject', int)
    progress_signal = pyqtSignal(int, int)
    transaction_progress_signal = pyqtSignal(int, int)
    lock_model_signal = pyqtSignal(bool)
    list_filling_signal = pyqtSignal(bool)
    ended_signal = pyqtSignal(int)
    request_action_signal = pyqtSignal(str, 'PyQt_PyObject')
    populate_pkgs_signal = pyqtSignal()
    action_timer_signal = pyqtSignal(bool)

    def __init__(self, mainw):
        super().__init__()
        self.main_window = mainw
        # instance variables
        self._ppas_json = {}
        self._team = "KXStudio-Debian" #"kxstudio-team"#
        # self.main_window.team_combo.addItem(self._team)
        self.main_window.arch_combo.addItem("amd64")
        self.main_window.arch_combo.addItem("i386")
        self._timer_num = 0
        self._timer = QTimer()
        # signals
        self.msg_signal.connect(self._message_user)  # , type=Qt.DirectConnection)
        self.log_signal.connect(self._log_msg)  # type=Qt.DirectConnection)
        self.progress_signal.connect(self._progress_changed)  # , type=Qt.DirectConnection)
        self.transaction_progress_signal.connect(self._transaction_progress_changed)  # , type=Qt.DirectConnection)
        self.lock_model_signal.connect(self._lock_model)  # , type=Qt.DirectConnection)
        self.list_filling_signal.connect(self._toggle_pkg_list_loading)  # , type=Qt.DirectConnection)
        self.ended_signal.connect(self._ended)
        self.request_action_signal.connect(self._request_action)
        self.populate_pkgs_signal.connect(self.populate_pkgs)
        self.action_timer_signal.connect(self._action_timer)

        self.pkg_model = PkgTVModel(['Installed', 'Pkg Name', 'Version', 'Team Name'],
                                    self._team.lower(),
                                    self.main_window.arch_combo.currentText().lower(),
                                    msg_signal=self.msg_signal,
                                    log_signal=self.log_signal,
                                    progress_signal=self.progress_signal,
                                    transaction_progress_signal=self.transaction_progress_signal,
                                    lock_model_signal=self.lock_model_signal,
                                    list_filling_signal=self.list_filling_signal,
                                    ended_signal=self.ended_signal,
                                    request_action_signal=self.request_action_signal,
                                    populate_pkgs_signal=self.populate_pkgs_signal,
                                    action_timer_signal=self.action_timer_signal)
        # initialises the dnf base, sack and query
        initialize_search()

        # cleans the installed section, which during testing has been gathering fluff.
        clean_installed()

        # connect
        self.connect()

    @property
    def team(self):
        return self._team

    @team.setter
    def team(self, name):
        self._team = name
        self.pkg_model.packages.lp_team = self._team
        self.populate_ppa_combo()
        self._pkg_model.populate_pkg_list(self.main_window.ppa_combo.currentData(),
                                          self.pkg_model.packages.arch)
        self.log_signal.emit("Connected to Launchpad", logging.INFO)

    @property
    def pkg_model(self):
        return self._pkg_model

    @pkg_model.setter
    def pkg_model(self, pm):
        self._pkg_model = pm

    @pyqtSlot(str)
    def _message_user(self, message):
        self.moveToThread(self.main_window.thread())
        self.main_window.message_user(message)

    @pyqtSlot('PyQt_PyObject', int)
    def _log_msg(self, exception, type):
        self.moveToThread(self.main_window.thread())
        self.main_window.log_msg(exception, type)

    @pyqtSlot(int)
    def _ended(self, cancellation):
        self.moveToThread(self.main_window.thread())
        self._progress_changed(0, 0)
        self._transaction_progress_changed(0, 0)
        if cancellation == ENDED_NTD:
            self._message_user("Nothing to do!")
        if cancellation == ENDED_ERR:
            self.pkg_model.packages.cancel_process = True
            self._message_user("Processing ended in error.  Check messages")
        if cancellation == ENDED_CANCEL:
            self.pkg_model.packages.cancel_process = True
            self._message_user("Processing cancelled by user")
            self._log_msg("Processing cancelled by user", logging.INFO)
        if cancellation == ENDED_SUCC:
            self._message_user("Processing successful!")
            self._log_msg("Processing successful!", logging.INFO)
        self.main_window.ended()

    @pyqtSlot(bool)
    def _toggle_pkg_list_loading(self, vis_bool):
        self.moveToThread(self.main_window.thread())
        self.main_window.toggle_pkg_list_loading(vis_bool)

    @pyqtSlot(int, int)
    def _progress_changed(self, amount, total):
        self.moveToThread(self.main_window.thread())
        self.main_window.progress_change(amount, total)

    @pyqtSlot(int, int)
    def _transaction_progress_changed(self, amount, total):
        self.moveToThread(self.main_window.thread())
        self.main_window.transaction_progress_changed(amount, total)

    @pyqtSlot(bool)
    def _lock_model(self, enabled):
        self.moveToThread(self.main_window.thread())
        self.main_window.lock_model(enabled)

    @pyqtSlot(str, 'PyQt_PyObject')
    def _request_action(self, msg, callback):
        self.moveToThread(self.main_window.thread())
        self.main_window.request_action(msg, callback)

    @pyqtSlot()
    def populate_pkgs(self):
        self.moveToThread(self.main_window.thread())
        self.main_window.populate_pkgs()

    @pyqtSlot(bool)
    def _action_timer(self, cont):
        """This is for the progress bar when dealing with undefined length
           actions, in packages.py"""
        if not self._timer.isActive() and cont is True:
            # self.moveToThread(self.main_window.thread())
            self._timer.setSingleShot(False)
            self._timer.timeout.connect(self._timer_fire)
            self._timer.start(500)
        if self._timer.isActive() and cont is False:
            self._timer.stop()

    def _timer_fire(self):
        self.moveToThread(self.main_window.thread())
        self._timer_num = self.main_window.progress_bar.value() + 1
        self._progress_changed(self._timer_num % 100, 100)

    def connect(self):
        try:
            self._pkg_model.packages.connect()
            self.main_window.reconnectBtn.setVisible(False)
            ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
            self.main_window._ppas_json = requests.get(ppas_link).json()
            self.main_window.ppa_combo.clear()
            for ppa in self.main_window._ppas_json['entries']:
                self.main_window.ppa_combo.addItem(ppa['displayname'], ppa['name'])
            self._pkg_model.populate_pkg_list(self.main_window.ppa_combo.currentData(),
                                              self.pkg_model.packages.arch)
            self.log_signal.emit("Connected to Launchpad", logging.INFO)
        except (httplib2.ServerNotFoundError, HTTPError) as e:
            self.main_window.reconnectBtn.setVisible(True)
            self.log_signal.emit(e, logging.ERROR)
            self.msg_signal.emit('Error connecting - see messages for more detail - check your internet connection. ')


def check_requirements():
    dependencies = []
    import distro
    if 'Fedora' in distro.linux_distribution():
        cfg['distro_type'] = 'rpm'
        dependencies = ['redhat-rpm-config', 'python3-devel', 'alien', 'rpm-build']
    else:
        cfg['distro_type'] = 'deb'
    if 'Fedora' in distro.linux_distribution() and cfg['distro_type'] == 'rpm':
        try:
            import rpm
            ts = rpm.TransactionSet()
            for requirement in dependencies:
                if not len(ts.dbMatch('name', requirement)):
                    print("Error, " + requirement + " must be installed for this program to be run")
                    sys.exit(1)
        except ModuleNotFoundError as e:
            pass
    return True


if __name__ == '__main__':
    if check_requirements():
        app = QApplication(sys.argv)
        myapp = lprpm_main_window.MainW()
        myapp.show()

        # timer = QTimer()
        # timer.timeout.connect(lambda:None)
        # timer.start(100)

        sys.exit(app.exec_())
