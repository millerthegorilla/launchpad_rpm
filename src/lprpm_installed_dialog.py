import logging
import logging.handlers

from PyQt5.QtWidgets import QDialog

from lprpm_conf import cfg, pkg_states
from ui.lprpm_installed_dialog_ui import UiLPRpmInstalledDialog
from treeview.installed_tvmodel import InstalledTVModel
from treeview.tvitem import TVItem

# TODO - add and sort out logging in MessagesWindow
class LPRpmInstalledDialog(QDialog):
    def __init__(self):
        super(LPRpmInstalledDialog, self).__init__()
        self.ui = UiLPRpmInstalledDialog()
        self.ui.setupUi(self)
        self.model = InstalledTVModel(['Installed', 'Pkg Name', 'Version', 'Team Name'])
        self.ui.tableView.setModel(self.model)

    def accept(self):
        self.hide()

    def reject(self):
        self.hide()

    def show(self):
        super().show()
        self.populate_model()

    def populate_model(self):
        for pkg in pkg_states['installled']:
            item = TVItem(pkg.values())