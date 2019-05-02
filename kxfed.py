#!/usr/bin/python3
import logging
import sys
import traceback
from threading import RLock

import httplib2
import requests
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, Qt, QTimer, QSortFilterProxyModel, QRegExp, QStringListModel
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QCompleter
from launchpadlib.errors import HTTPError

from tvmodel import TVModel
from kfconf import cfg, cache, pkg_states, ENDED_ERR, ENDED_CANCEL, ENDED_SUCC
from kxfed_prefs import KxfedPrefsDialog
from kxfed_ui import Ui_MainWindow
from kxfedmsgsdialog import KxfedMsgsDialog


# TODO add installed packages to config
# TODO send in correct path for build_rpm.sh
# TODO to build_rpms.sh, unless relative path is ok?
class MainW(QMainWindow, Ui_MainWindow, QApplication):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.lock = RLock()

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

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

        # preferences dialog
        self.kxfed_prefs_dialog = KxfedPrefsDialog()
        self.btn_edit_config.triggered.connect(self.show_prefs)

        # messages dialog
        self.kxfed_msgs_dialog = KxfedMsgsDialog()
        self.btn_show_messages.triggered.connect(self.show_msgs)

        # connection button
        self.reconnectBtn.setVisible(False)

        # kxfed object - controller
        self.kxfed = Kxfed(self)

        self.reconnectBtn.pressed.connect(self.kxfed.connect)
        self.pkgs_tableView.setModel(self.kxfed.pkg_model)
        self.pkgs_tableView.horizontalHeader().setStretchLastSection(True)
        self.pkgs_tableView.setStyleSheet("QTableView::QCheckBox::indicator { position : center; }")
        self.pkgs_tableView.setSortingEnabled(True)

        self.ppa_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.arch_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.install_btn.clicked.connect(self.install_pkgs_button)
        self.install_btn.setText('Process Packages')
        self.btn_quit.triggered.connect(self.close)

        self.progress_bar.setVisible(False)
        self.transaction_progress_bar.setVisible(False)

        # connection button
        self.reconnectBtn.setVisible(False)
        self.reconnectBtn.pressed.connect(self.kxfed.connect)

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

        self.autoSearch.setPlaceholderText("Search table")

        self.autoSearch.textChanged.connect(self._filter)
        self.autoSearch.textEdited.connect(self._change_proxy_model)
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self.kxfed.pkg_model)
        self._proxy_model.setFilterKeyColumn(1)
        self._proxy_model.lessThan = self._less_than

        self.team_line_edit.textChanged.connect(self._team_text)
        self.qcomplete = QCompleter()
        self.qcomplete.highlighted.connect(self._chosen)

    def _chosen(self, text):
        self.kxfed.team = text
        self.qcomplete.popup().hide()

    def _team_text(self, text):
        if len(text) > 3:
            model = QStringListModel()
            model.setStringList([ x.name for x in self.kxfed.pkg_model.packages.launchpad.people.findTeam(text=text)])
            self.qcomplete.setModel(model)
            self.team_line_edit.setCompleter(self.qcomplete)

    def _less_than(self, index0, index1):
        # index0 = self._proxy_model.mapToSource(index0)
        # index1 = self._proxy_model.mapToSource(index1)
        if index0.column() == 0:
            return self.kxfed.pkg_model.item(index0.row(), index0.column()).checkState() > \
                   self.kxfed.pkg_model.item(index1.row(), index1.column()).checkState()
        else:
            return self.kxfed.pkg_model.item(index0.row(), index0.column()) < \
                   self.kxfed.pkg_model.item(index1.row(), index1.column())

    def _change_proxy_model(self):
        self.pkgs_tableView.setModel(self.kxfed.pkg_model)

    def _filter(self, text):
        if text == "":
            self.pkgs_tableView.setModel(self.kxfed.pkg_model)
        else:
            self.pkgs_tableView.setModel(self._proxy_model)
            search = QRegExp(text,
                             Qt.CaseInsensitive,
                             QRegExp.RegExp)
            self._proxy_model.setFilterRegExp(search)
            self._proxy_model.invalidateFilter()

    def refresh_cache(self):
        self.toggle_pkg_list_loading(True)
        cache.invalidate(hard=True)
        self.populate_pkgs()

    def show_prefs(self):
        self.kxfed_prefs_dialog.show()

    def show_msgs(self):
        self.kxfed_msgs_dialog.show()

    def lock_model(self, enabled):
        self.pkgs_tableView.setEnabled(enabled)

    def ended(self):
        self.install_btn.setText('Process Packages')
        self.install_btn.clicked.disconnect()
        self.install_btn.clicked.connect(self.install_pkgs_button)

    def toggle_pkg_list_loading(self, vis_bool):
        self.load_label.setVisible(vis_bool)
        if vis_bool:
            self.load_label.move(self.pkgs_tableView.x() + self.pkgs_tableView.width() / 2 - self.load_label.width() / 2,
                                 self.pkgs_tableView.y() + self.pkgs_tableView.height() / 2)
            self._movie.start()
        else:
            self._movie.stop()
            self.pkgs_tableView.resizeColumnsToContents()
            self.pkgs_tableView.resizeRowsToContents()

    def progress_change(self, amount, total):
        # self.lock.acquire(blocking=True)
        if amount == 0 or total == 0:
            self.progress_bar.setVisible(False)
        else:
            # TODO perhaps obtain a lock somewhere in this function
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(amount)

    # self.lock.release()

    def transaction_progress_changed(self, amount, total):
        # self.lock.acquire(blocking=True)
        if amount == 0 and total == 0:
            self.transaction_progress_bar.setVisible(False)
            self.transaction_progress_bar.setValue(0)
        else:
            self.transaction_progress_bar.setVisible(True)
            self.transaction_progress_bar.setMaximum(total)
            self.transaction_progress_bar.setValue(amount)

    # self.lock.release()

    def message_user(self, msg):
        self.lock.acquire(blocking=True)
        self.statusbar.showMessage(msg, msecs=8000)
        self.statusbar.update()
        self.processEvents()
        self.lock.release()

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
            self.load_label.setVisible(True)
            self.kxfed.pkg_model.populate_pkg_list(
                self.ppa_combo.itemData(self.ppa_combo.currentIndex()),
                self.arch_combo.currentText())
        except Exception as e:
            self.log_msg(e, logging.ERROR)

    def install_pkgs_button(self):
        try:
            self.install_btn.setText('Cancel')
            self.install_btn.clicked.disconnect()
            self.install_btn.clicked.connect(self.cancel_process_button)
            self.kxfed.pkg_model.packages.install_pkgs_button()
        except Exception as e:
            self.log_msg(e, logging.ERROR)

    def cancel_process_button(self):
        self.kxfed.pkg_model.packages.cancel()

    def request_action(self, msg, callback):
        result = QMessageBox.question(QMessageBox(),
                                      "Confirm Action...",
                                      msg,
                                      QMessageBox.Yes | QMessageBox.No)

        if result == QMessageBox.Yes:
            callback()

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
                self.log_signal.emit(e, logging.CRITICAL)
            event.accept()


class Kxfed(QThread):
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

        self.pkg_model = TVModel(['Installed', 'Pkg Name', 'Version', 'Description'],
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
        # self.pkg_model.setSortRole(TVITEM_ROLE)

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
        self._timer = QTimer()
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._timer_fire)
        if self._timer.isActive() and cont is False:
            self._timer.stop()
        elif not self._timer.isActive() and cont is True:
            self._timer.start(500)

    def _timer_fire(self):
        self._timer_num += 1
        self.progress_signal.emit(self._timer_num % 100, 100)

    def connect(self):
        try:
            self._pkg_model.packages.connect()
            self.main_window.reconnectBtn.setVisible(False)
            self.populate_ppa_combo()
            self._pkg_model.populate_pkg_list(self.main_window.ppa_combo.currentData(),
                                              self.pkg_model.packages.arch)
            self.log_signal.emit("Connected to Launchpad", logging.INFO)
        except (httplib2.ServerNotFoundError, HTTPError) as e:
            self.main_window.reconnectBtn.setVisible(True)
            self.log_signal.emit(e, logging.ERROR)
            self.msg_signal.emit('Error connecting - see messages for more detail - check your internet connection. ')

    def populate_ppa_combo(self):
        try:
            ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
            self.main_window._ppas_json = requests.get(ppas_link).json()
        except requests.HTTPError as e:
            self.log_signal.emit(e, logging.CRITICAL)
        self.main_window.ppa_combo.clear()
        for ppa in self.main_window._ppas_json['entries']:
            self.main_window.ppa_combo.addItem(ppa['displayname'], ppa['name'])


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
        myapp = MainW()
        myapp.show()

        timer = QTimer()
        timer.timeout.connect(lambda:None)
        timer.start(100)

        sys.exit(app.exec_())
