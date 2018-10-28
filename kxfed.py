import sys, os, requests
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from kxfed_ui import Ui_MainWindow
from treemodel import TreeModel
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
        self.arch_combo.addItem("x86")
        self.arch_combo.addItem("amd64")

        self.pkg_model = TreeModel(['Installed', 'Pkg Name', 'Version', 'Description'],
                                   Packages(self.team_combo.currentText(),
                                            self.arch_combo.currentText()))
        self.packages_treeview.setModel(self.pkg_model)
        self._ppas_json = ""
        self.populate_ppa_combo()

    def populate_ppa_combo(self):
        self._ppas_json = requests.get(self.pkg_model
                                       .packages
                                       .team
                                       .ppas_collection_link).json()
        for ppa in self._ppas_json['entries']:
            self.ppa_combo.addItem(ppa['displayname'])

    def populate_pkgs(self):
        # treemodel stuff
        self.pkg_model.packages.ppa = self.ppa_combo.currentText()
        self.pkg_model.populate_pkgs


if __name__ == '__main__':

    app = QApplication(sys.argv)
    myapp = MainW()
    myapp.show()
    sys.exit(app.exec_())