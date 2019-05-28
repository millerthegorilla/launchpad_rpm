#!/usr/bin/python3
import logging
import traceback
from threading import RLock

from PyQt5.QtCore import Qt, QSortFilterProxyModel, QRegExp, QStringListModel, QEvent
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QCompleter
from os import scandir, remove
from lprpm_conf import cfg, cache, pkg_states, rpms_dir, debs_dir
from lprpm_prefs_dialog import LPRpmPrefsDialog
from ui.lprpm_main_window_ui import Ui_MainWindow
from lprpm_msgs_dialog import LPRpmMsgsDialog
from lprpm_installed_dialog import LPRpmInstalledDialog
from lprpm_first_run_dialog import LPRpmFirstRunDialog
from lprpm import LPRpm
from multiprocessing.dummy import Pool as ThreadPool
import time
import pickle


class MainW(QMainWindow, Ui_MainWindow, QApplication):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.lock = RLock()
        self._thread_pool = ThreadPool(10)

        self._movie = QMovie("./assets/loader.gif")
        self.load_label.setMovie(self._movie)
        self.load_label.setMinimumWidth(200)
        self.load_label.setMinimumHeight(20)

        # preferences dialog
        self.lprpm_prefs_dialog = LPRpmPrefsDialog()
        self.btn_edit_config.triggered.connect(self.show_prefs)

        # messages dialog
        self.lprpm_msgs_dialog = LPRpmMsgsDialog()
        self.btn_show_messages.triggered.connect(self.show_msgs)
        self.pkgs_tableView.horizontalHeader().setStretchLastSection(True)
        self.pkgs_tableView.setStyleSheet("QTableView::QCheckBox::indicator { position : center; }")

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

        # preferences dialog
        #self.lprpm_prefs_dialog = LPRpmPrefsDialog()
        self.btn_edit_config.triggered.connect(self.show_prefs)

        # messages dialog
        self.lprpm_msgs_dialog = LPRpmMsgsDialog()
        self.btn_show_messages.triggered.connect(self.show_msgs)

        # installed dialog
        #self.lprpm_installed_dialog = LPRpmInstalledDialog()
        self.lprpm_installed_dialog = None
        self.btn_show_installed.triggered.connect(self.show_installed)

        # menu clear buttons
        self.btn_clear_converted.triggered.connect(self.clear_converted)
        self.btn_clear_downloaded.triggered.connect(self.clear_downloaded)

        # connection button
        self.reconnectBtn.setVisible(False)

        # kxfed object - controller
        self.lprpm = LPRpm(self)

        self.reconnectBtn.pressed.connect(self.lprpm.connect)
        self.pkgs_tableView.setModel(self.lprpm.pkg_model)
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
        self.reconnectBtn.pressed.connect(self.lprpm.connect)

        # refresh cache button
        self.btn_refresh_cache.triggered.connect(self.refresh_cache)

        self.autoSearch.setPlaceholderText("Search table")

        self.autoSearch.textChanged.connect(self._filter)
        self.autoSearch.textEdited.connect(self._change_proxy_model)
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self.lprpm.pkg_model)
        self._proxy_model.setFilterKeyColumn(1)
        self._proxy_model.lessThan = self._less_than

        self.team_line_edit.textChanged.connect(self._team_text)
        #self.team_line_edit.installEventFilter(self.team_line_edit)
        #self.team_line_edit.textEdited.connect(self._team_text)
        self.qcomplete = QCompleter()
        self.qcomplete.setModelSorting(QCompleter.CaseSensitivelySortedModel)
        #self.qcomplete.activated.connect(self._chosen)
        # if cfg['cache']['initiated'] is None:
        #     self._first_run_dialog = LPRpmFirstRunDialog()
        with open('../teamnames.pkl', 'rb') as f:
            self._team_data_list = pickle.load(f)
        self.completer_model = QStringListModel()
        self.completer_model.setStringList(self._team_data_list)
        self.qcomplete.setModel(self.completer_model)
        self.team_line_edit.setCompleter(self.qcomplete)
        self._team_data_wrapper()

        self.team_line_edit.returnPressed.connect(self._team_text_return_slot)

    # def eventFilter(self, source, event):
    #     if event.type is QEvent.KeyPress and source is self.team_line_edit:
    #         bob = event.key()
    #         # self.lprpm.team = self.team_line_edit.text()
    #     return super().eventFilter(source, event)

    def _team_text_return_slot(self):
        name = self.completer_model.data(self.qcomplete.currentIndex(), 0)
        if name is None:
            self.lprpm.team = self.team_line_edit.text()
        else:
            self.lprpm.team = name

    def _chosen(self, text):
        self.lprpm.team = text
        self.qcomplete.popup().hide()

    def _team_text(self, text):
        self.qcomplete.setModel(self.completer_model)

    def _team_data_wrapper(self):
        if cfg['cache']['initiated'] is None:
            cfg['cache']['initiated'] = time.time()
        self._thread_pool.apply_async(self._team_data, (cfg['cache']['initiated'],), callback=self._team_data_obtained)

    def _team_data_obtained(self, team_list):
        #self.message_user("Finished updating list of teams from launchpad.  See messages.")
        self.log_msg("Finished initialising team list, The result is cached and you can renew"
                     "caches if you wish to reinstall this list", level=logging.INFO)
        with open('teamnames.pkl', 'wb') as f:
            pickle.dump(team_list, f)
        self._team_data_list = team_list

    #@cache.cache_on_arguments()
    def _team_data(self, initiation_time):
        #self.message_user("Updating list of teams from launchpad.")
        self.log_msg("Initialising team list. The result is cached and you can renew"
                     "caches if you wish to reinitialise this list", level=logging.INFO)
        return [x.name for x in self.lprpm.pkg_model.packages.launchpad.people.findTeam(text="")]

    def _less_than(self, index0, index1):
        # index0 = self._proxy_model.mapToSource(index0)
        # index1 = self._proxy_model.mapToSource(index1)
        if index0.column() == 0:
            return self.lprpm.pkg_model.item(index0.row(), index0.column()).checkState() > \
                   self.lprpm.pkg_model.item(index1.row(), index1.column()).checkState()
        else:
            return self.lprpm.pkg_model.item(index0.row(), index0.column()) < \
                   self.lprpm.pkg_model.item(index1.row(), index1.column())

    def _change_proxy_model(self):
        self.pkgs_tableView.setModel(self.lprpm.pkg_model)

    def _filter(self, text):
        if text == "":
            self.pkgs_tableView.setModel(self.lprpm.pkg_model)
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
        self.lprpm_prefs_dialog.show()

    def show_msgs(self):
        self.lprpm_msgs_dialog.show()

    def show_installed(self):
        self.lprpm.installed_dialog = LPRpmInstalledDialog(self.lprpm.team, self.lprpm.pkg_model)
        self.lprpm.installed_changed_signal.connect(self.lprpm.installed_dialog.populate_model)
        self.lprpm.installed_dialog.show()

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
        if amount == 0 or total == 0:
            self.progress_bar.setVisible(False)
        else:
            # TODO perhaps obtain a lock somewhere in this function
            # TODO rather than the lock around the call to this function
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(amount)

    def transaction_progress_changed(self, amount, total):
        if amount == 0 and total == 0:
            self.transaction_progress_bar.setVisible(False)
            self.transaction_progress_bar.setValue(0)
        else:
            self.transaction_progress_bar.setVisible(True)
            self.transaction_progress_bar.setMaximum(total)
            self.transaction_progress_bar.setValue(amount)

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
            self.lprpm_msgs_dialog.log(log_record=log_record)
            self.message_user("Error.  See messages.")
        else:
            self.lprpm_msgs_dialog.log(msg=str(e), level=level)

    def populate_pkgs(self):
        try:
            self.load_label.setVisible(True)
            self.lprpm.pkg_model.populate_pkg_list(
                self.ppa_combo.itemData(self.ppa_combo.currentIndex()),
                self.arch_combo.currentText())
        except Exception as e:
            self.log_msg(e, logging.ERROR)

    def install_pkgs_button(self):
        try:
            self.install_btn.setText('Cancel')
            self.install_btn.clicked.disconnect()
            self.install_btn.clicked.connect(self.cancel_process_button)
            self.lprpm.pkg_model.packages.install_pkgs_button()
        except Exception as e:
            self.log_msg(e, logging.ERROR)

    def cancel_process_button(self):
        self.lprpm.pkg_model.packages.cancel()

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

    @staticmethod
    def clear_downloaded():
        with scandir(debs_dir) as it:
            for file in it:
                remove(file.path)

    @staticmethod
    def clear_converted():
        with scandir(rpms_dir) as it:
            for file in it:
                remove(file.path)
