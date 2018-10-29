import sys, os, requests, logging
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import pyqtSlot
from kxfed_ui import Ui_MainWindow
from listmodel import ListModel
from packages import Packages


# TODO read about populating treeview or change to listview
# TODO make the call to populate treeview here in this file
# TODO but make the call to pkg_model.
class MainW (QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        # cachedir for launchpadlib - needs to be session level?
        cachedir = "cachedir"
        if not os.path.exists(cachedir):
            os.mkdir(cachedir)
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
        self.label.hide()
        movie = QMovie("./assets/loader.gif")
        self.label.setMovie(movie)
        self.pkg_model.list_filled.connect(self.show_progress)

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

    @pyqtSlot(bool)
    def show_progress(self, hide):
        if hide is True:
            self.label.hide()
        else:
            self.label.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    myapp = MainW()
    myapp.show()
    sys.exit(app.exec_())