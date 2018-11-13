import sys, requests, logging, traceback
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import pyqtSlot
from kxfed_ui import Ui_MainWindow
import kfconf
from tvmodel import TVModel


# TODO add installed packages to config
# TODO add menu bar to ui and set config opts, expire cache etc.
# TODO list model line 44, use self.__result, instead of callback
# TODO to populate listview, using event property of result...
class MainW (QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        # instance variables
        self.__ppas_json = ""
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

        # progress label
        self.load_label.setVisible(True)
        self.__movie = QMovie("./assets/loader.gif")
        self.__movie.start()
        self.load_label.setMovie(self.__movie)

        # progress bar
        self.progress_bar.setVisible(False)
        self._download_total = 0
        self._download_current = 0

        # status bar
        self.label = QLabel()
        self.statusbar.addWidget(self.label)

        # signals
        self.pkg_model.list_filled.connect(self.toggle_pkg_list_loading)
        self.pkg_model.message.connect(self.message_user)
        self.pkg_model.packages.progress_adjusted.connect(self.progress_changed)
        #        self.pkg_model.packages.message.connect(self.message_user)
        self.pkg_model.packages.exception.connect(self._exception)
        # user signals
        self.ppa_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.install_btn.clicked.connect(self.install_pkgs)

        # initiate connection and populate combo
        try:
            self.pkg_model.connect()
            self.populate_ppa_combo()
        except requests.HTTPError as e:
            logging.log(logging.ERROR, str(e))
            self.message_user(traceback.format_exc())

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
                logging.log(logging.CRITICAL, str(e))
            event.accept()

    def populate_ppa_combo(self):
        try:
            ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
            self.__ppas_json = requests.get(ppas_link).json()
        except requests.HTTPError as e:
            logging.log("error", e.strerror)
            self.message_user(e.strerror)
        for ppa in self.__ppas_json['entries']:
            self.ppa_combo.addItem(ppa['displayname'], ppa['name'])

    def install_pkgs(self):
        try:
            self.pkg_model.action_pkgs()
        except Exception as e:
            logging.log(logging.ERROR, str(e))
            self.message_user(traceback.format_exc())

    def populate_pkgs(self):
        try:
            self.pkg_model.populate_pkg_list(self.ppa_combo.itemData(self.ppa_combo.currentIndex()))
        except Exception as e:
            logging.log(logging.ERROR, str(e))
            self.message_user(traceback.format_exc())

    @pyqtSlot()
    def toggle_pkg_list_loading(self):
        self.load_label.setVisible(not self.load_label.isVisible())
        if self.load_label.isVisible():
            self.__movie.start()
        else:
            self.__movie.stop()
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
            self.statusbar.showMessage("Downloading Packages", 100)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self._download_total)
            self.progress_bar.setValue(self._download_current)

    @pyqtSlot(str)
    def message_user(self, msg):
        self.label.setText(msg)

    @pyqtSlot('PyQt_PyObject')
    def _exception(self, ex):
        raise type(ex)(traceback.format_exc())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = MainW()
    myapp.show()
    sys.exit(app.exec_())
