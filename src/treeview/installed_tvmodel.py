#!/usr/bin/env python

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtGui import QBrush, QColor

from treeview.tvmodel import TVModel
from treeview.tvitem import TEAMNAME_ROLE, PPA_ROLE, TVITEM_ROLE


class InstalledTVModel(TVModel):
    list_filled_signal = pyqtSignal(list)
    list_changed_signal = pyqtSignal(str, str)
    highlight_color = QColor(255, 204, 204)
    highlight_brush = QBrush()

    def __init__(self, headers, current_team, model):
        super(InstalledTVModel, self).__init__(headers)
        self.current_team = current_team
        self.main_window_model = model
        TVModel.highlight_brush.setColor(TVModel.highlight_color)
        TVModel.highlight_brush.setStyle(Qt.DiagCrossPattern)

    def itemChanged(self, item):
        super().itemChanged(item)
        pkg = item.data(TVITEM_ROLE)
        if pkg.team.lower() == self.current_team.lower():
            try:
                row = self.main_window_model.findItems(pkg.name, column=1)[0].row()
                foreign_table_item = self.main_window_model.itemFromIndex(self.main_window_model.index(row, 0))
                if foreign_table_item.checkState() == Qt.Checked:
                    foreign_table_item.setCheckState(Qt.Unchecked)
                elif foreign_table_item.checkState() == Qt.Unchecked:
                    foreign_table_item.data(TVITEM_ROLE)._installed = Qt.Checked
                    foreign_table_item.setCheckState(Qt.Checked)
            except Exception as e:
                pass


