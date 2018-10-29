import sys, os, requests, logging
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import pyqtSlot
from kxfed_ui import Ui_MainWindow
from listmodel import ListModel
from packages import Packages
from config_init import KxFedConfig


# TODO make tree cache, make config for installed files etc.
# investigate if cache is better with config or pickle
class MainW (QMainWindow, Ui_MainWindow):
    def __init__(self):
        global cfg
        QMainWindow.__init__(self)
        self.setupUi(self)

        # config
        KxFedConfig()

        self.ppa_combo.currentIndexChanged.connect(self.populate_pkgs)
        self.team = "kxstudio-debian"
        self.team_combo.addItem(self.team)
        self.arch_combo.addItem("amd64")
        self.arch_combo.addItem("x86")
        self.pkg_model = ListModel(['Installed', 'Pkg Name', 'Version', 'Description'],
                                   Packages(self.team_combo.currentText().lower(),
                                            self.arch_combo.currentText().lower()))
        self.pkgs_listView.setModel(self.pkg_model)
        self._ppas_json = ""
        self.populate_ppa_combo()
        self.load_label.setVisible(True)
        self.__movie = QMovie("./assets/loader.gif")
        self.__movie.start()
        self.load_label.setMovie(self.__movie)
        self.pkg_model.list_filled.connect(self.show_progress)

    def closeEvent(self, event):
        """
        clean up :
            invalidate ie delete cache file
        :param event:
        :return:
        """
        result = QMessageBox.question(self,
                                      "Confirm Exit...",
                                      "Are you sure you want to exit ?",
                                      QMessageBox.Yes | QMessageBox.No)
        event.ignore()

        if result == QMessageBox.Yes:
            event.accept()

    def populate_ppa_combo(self):
        try:
            ppas_link = self.pkg_model.packages.lp_team.ppas_collection_link
            self._ppas_json = requests.get(ppas_link).json()
        except requests.HTTPError as http_error:
            logging.log("error", http_error.response)
        for ppa in self._ppas_json['entries']:
            self.ppa_combo.addItem(ppa['displayname'], ppa['name'])

    def populate_pkgs(self):
        self.pkg_model.populate_pkg_list(self.ppa_combo.itemData(self.ppa_combo.currentIndex()))

    @pyqtSlot()
    def show_progress(self):
        self.load_label.setVisible(not self.load_label.isVisible())
        if self.load_label.isVisible():
            self.__movie.start()
        else:
            self.__movie.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = MainW()
    myapp.show()
    sys.exit(app.exec_())