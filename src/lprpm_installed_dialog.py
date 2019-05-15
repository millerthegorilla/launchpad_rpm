import logging
import logging.handlers

from PyQt5.QtWidgets import QDialog, QAbstractScrollArea, QDialogButtonBox
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QBrush
from lprpm_conf import pkg_states
from ui.lprpm_installed_dialog_ui import UiLPRpmInstalledDialog
from treeview.installed_tvmodel import InstalledTVModel
from treeview.tvitem import TVItem


# TODO - add and sort out logging in MessagesWindow
class LPRpmInstalledDialog(QDialog):
    def __init__(self, current_team, model):
        super(LPRpmInstalledDialog, self).__init__()
        self.ui = UiLPRpmInstalledDialog()
        self.ui.setupUi(self)
        self.ui.tableView.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents)
        self.pkg_model = model
        self.model = InstalledTVModel(['Installed', 'Pkg Name', 'Version', 'Team Name'], current_team, model)
        self.ui.tableView.setModel(self.model)
        self.ui.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

    def apply(self):
        self.pkg_model.packages.install_pkgs_button()

    def reject(self):
        self.model.removeRows(0, self.model.rowCount())
        self.hide()
        del self

    def show(self):
        super().show()
        self.populate_model()

    def populate_model(self):
        self.model.removeRows(0, self.model.rowCount())
        for team in pkg_states['installed']:
            for ppa in pkg_states['installed'][team]:
                for pkg in pkg_states['installed'][team][ppa]:
                    item = TVItem([pkg_states['installed'][team][ppa][pkg]['build_link'],
                                   ppa,
                                   pkg_states['installed'][team][ppa][pkg]['name'],
                                   pkg_states['installed'][team][ppa][pkg]['version'],
                                   team,
                                   team,
                                   pkg_states['installed'][team][ppa][pkg]['id']])
                    item._installed = Qt.Checked
                    item._install_state.setCheckState(item._installed)
                    self.model.appendRow(item.row)
            for team in pkg_states['uninstalling']:
                for ppa in pkg_states['uninstalling'][team]:
                    for pkg in pkg_states['uninstalling'][team][ppa]:
                        item = TVItem([pkg_states['uninstalling'][team][ppa][pkg]['build_link'],
                                       ppa,
                                       pkg_states['uninstalling'][team][ppa][pkg]['name'],
                                       pkg_states['uninstalling'][team][ppa][pkg]['version'],
                                       team,
                                       team,
                                       pkg_states['uninstalling'][team][ppa][pkg]['id']])
                        item._installed = Qt.Checked
                        item._install_state.setCheckState(item._installed)
                        self.model.appendRow(item.row)
                        display_item = self.model.item(self.model.rowCount() - 1, 0)
                        display_item.setBackground(QBrush(Qt.red))
            self.list_changed()

    def list_changed(self):
        self.ui.tableView.resizeColumnsToContents()
