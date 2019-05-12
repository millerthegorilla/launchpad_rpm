#!/usr/bin/env python

import multiprocessing.dummy
import logging
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtGui import QBrush, QColor

from lprpm_conf import cfg, \
    pkg_states, delete_ppa_if_empty, \
    add_item_to_section, pkg_search, check_installed
from treeview.tvmodel import TVModel
from treeview.tvitem import TVItem


class InstalledTVModel(TVModel):
    list_filled_signal = pyqtSignal(list)
    list_changed_signal = pyqtSignal(str, str)
    highlight_color = QColor(255, 204, 204)
    highlight_brush = QBrush()

    def __init__(self, headers):
        super(InstalledTVModel, self).__init__(headers)

        TVModel.highlight_brush.setColor(TVModel.highlight_color)
        TVModel.highlight_brush.setStyle(Qt.DiagCrossPattern)

