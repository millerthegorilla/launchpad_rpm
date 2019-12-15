#!/usr/bin/python3
import logging
import sys

import httplib2
import requests
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, QTimer, Qt
from PyQt5.QtWidgets import QApplication
from launchpadlib.errors import HTTPError

from treeview.pkg_tvmodel import PkgTVModel
from lprpm_conf import cfg, initialize_search, \
                        clean_installed, ENDED_ERR, ENDED_CANCEL, \
                        ENDED_SUCC, ENDED_NTD
import pickle
import logging
import lprpm_main_window
from lprpm_first_run_dialog import LPRpmFirstRunDialog
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool


class LPRpm(QThread):
    '''
    Main controller class, extends QThread to allow it to use signalling.
    Mainwindow constructs controller object, which constructs a package treeview model.
    The pkg_tv_model then contains a packages object which does the main work of
    interacting with launchpad.
    '''
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
    installed_changed_signal = pyqtSignal()
    team_signal = pyqtSignal()

    def __init__(self, mainw, ):
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
        self._thread_pool = ThreadPool(10)
        # signals
        self.team_signal.connect(self._team_data_wrapper)
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
        self.installed_dialog = None
        self.first_run_dialog = None
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
                                    action_timer_signal=self.action_timer_signal,
                                    installed_changed_signal=self.installed_changed_signal)

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
        try:
            self.pkg_model.packages.lp_team = name
        except ValueError as v:
            self.msg_signal.emit("Unable to find team with that name")
            self.log_signal.emit("Unable to find team with that name", logging.INFO)
            return
        self._team = name
        if self.populate_ppa_combo() is not 0:
            self._pkg_model.populate_pkg_list(self.main_window.ppa_combo.currentData(),
                                              self.pkg_model.packages.arch)
        else:
            # try the standard root ppa archive
            self._pkg_model.populate_pkg_list('ppa',
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

    @pyqtSlot('PyQt_PyObject')
    def _set_team_list(self):
        """called as a signal from first_run_dialog"""
        self.main_window.set_team_name()

    def check_renew(self):
        renew_cache = False
        if cfg['initialised']['renew_period'] != "None":
            day = int(cfg['initialised']['day'])
            month = int(cfg['initialised']['month'])
            year = int(cfg['initialised']['year'])

        if cfg['initialised']['renew_period'] == "None":
            renew_cache = True
        elif cfg['initialised']['renew_period'] == "every_time":
            renew_cache = True
        elif cfg['initialised']['renew_period'] == "daily":
            if month != datetime.now().date().month:
                renew_cache = True
            elif day != datetime.now().date().day:
                renew_cache = True
        elif cfg['initialised']['renew_period'] == "monthly":
            if month != datetime.now().date().month:
                renew_cache = True
        elif cfg['initialised']['renew_period'] == "6month":
            if datetime.now().date().year != year:
                if ((12 - month) + datetime.now().date().month) > 6:
                    renew_cache = True
            elif (datetime.now().date().month - month) > 6:
                renew_cache = True

        if renew_cache is True:
            if cfg['initialised']['renew_period'] != "None":
                renew_cache = False
                cfg['initialised']['month'] = datetime.now().date().month
                cfg['initialised']['day'] = datetime.now().date().day
                cfg['initialised']['year'] = datetime.now().date().year

            self.first_run_dialog = LPRpmFirstRunDialog(mainw=self.main_window, team_signal=self.team_signal, log_signal=self.log_signal,
                                                        message_user_signal=self.msg_signal, cache_renew=renew_cache)
            self.first_run_dialog.setWindowModality(Qt.ApplicationModal)
            self.first_run_dialog.show()
        else:
            self.main_window.set_team_name()

    def _timer_fire(self):
        self.moveToThread(self.main_window.thread())
        self._timer_num = self.main_window.progress_bar.value() + 1
        self._progress_changed(self._timer_num % 100, 100)

    def populate_ppa_combo(self):
        ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
        self.main_window._ppas_json = requests.get(ppas_link).json()
        self.main_window.ppa_combo.clear()
        for ppa in self.main_window._ppas_json['entries']:
            self.main_window.ppa_combo.addItem(ppa['displayname'], ppa['name'])
        return len(self.main_window._ppas_json['entries'])

    def connect(self):
        '''
        function to connect to launchpad.net rest api
        calls check_renew to check prefs for renewing teamname list when connected
        '''
        try:
            self.main_window.reconnectBtn.setVisible(False)
            self._pkg_model.packages.connect()
            self.populate_ppa_combo()
            self._pkg_model.populate_pkg_list(self.main_window.ppa_combo.currentData(),
                                              self.pkg_model.packages.arch)
            self.log_signal.emit("Connected to Launchpad", logging.INFO)
            self._message_user("Connected to Launchpad")
            self.check_renew()
        except (httplib2.ServerNotFoundError, HTTPError) as e:
            self.main_window.reconnectBtn.setVisible(True)
            self.log_signal.emit(e, logging.ERROR)
            self.msg_signal.emit('Error connecting - see messages for more detail - check your internet connection. ')

    def _team_data_wrapper(self):
        '''
        wrapper function to call the launchpad name obtaining function using async call
        '''
        self._message_user("Updating list of teams from launchpad.")
        self._log_msg("Initialising team list. The result is cached and you can renew"
                      "caches if you wish to reinitialise this list", logging.INFO)
        self._thread_pool.apply_async(self._team_data, callback=self._team_data_obtained)

    def _team_data_obtained(self, bob):
        '''
        callback from async function.  dumps list as pickle
        :param team_list: list of teamnames from launchpad
        :type team_list: list
        '''
        self._message_user("Finished updating list of teams from launchpad. Result is cached. "
                           "See preferences to renew")
        self._log_msg("Finished initialising team list, The result is cached and you can renew"
                      "caches if you wish to reinstall this list", logging.INFO)
        self.first_run_dialog.hide()
        self.main_window.set_team_name()

    def _team_data(self):
        '''
        function to obtain list of names of teams from Launchpad.net
        takes a long time...
        :return: list of team names
        :rtype: list
        '''
        try:
            team_list = self.pkg_model.packages.launchpad.people.findTeam(text="")
            team_name_list = [x.name for x in team_list]
            with open('teamnames.pkl', 'wb') as f:
                pickle.dump(team_name_list, f)
        except Exception as e:
            self.log_signal.emit(e, logging.INFO)


# TODO change to use dnf
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

        sys.exit(app.exec_())
