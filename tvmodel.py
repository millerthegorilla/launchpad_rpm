#!/usr/bin/env python

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import multiprocessing.dummy
from packages import Packages
import subprocess
import kfconf
from kfconf import TVITEM_ROLE
from tvitem import TVItem


class TVModel(QStandardItemModel):

    list_filled = pyqtSignal()

    def __init__(self, headers, team, arch, *args):
        # passing in conf to avoid static for threading.
        super().__init__(*args)
        self.__packages = Packages(team, arch)
        # self.packages.get(self._setupModelData_) do this when ppa combo is selected
        self.setHorizontalHeaderLabels(headers)
        self.__pool = multiprocessing.dummy.Pool(10)
        self.__result = None
        self.itemChanged.connect(TVModel.on_item_changed)

    @property
    def packages(self):
        return self.__packages

    def populate_pkg_list(self, ppa):
        self.list_filled.emit()
        self.removeRows(0, self.rowCount())
        self.__result = self.__pool.apply_async(self.__packages.populate_pkgs,
                                                (ppa,),
                                                callback=self.pkg_list_complete)

    def pkg_list_complete(self, pkgs):
        for pkg in pkgs:
            pkg = TVItem(pkg)
            if pkg.build_link in kfconf.cfg['installed']:
                pkg.installed = Qt.Checked
            else:
                pkg.installed = Qt.Unchecked
            self.appendRow(pkg.row)

        self.list_filled.emit()

    @staticmethod
    def on_item_changed(item):
        pkg = item.data(TVITEM_ROLE)
        if item.isCheckable():
            if pkg.installed == Qt.Unchecked:
                item.setCheckState(Qt.PartiallyChecked)
            if item.checkState() == Qt.Unchecked:
                if pkg.installed == Qt.PartiallyChecked:
                    kfconf.cfg['tobeinstalled'][pkg.ppa].pop(pkg.id)
                    TVModel.delete_ppa_if_empty('tobeinstalled', pkg.ppa)
            if item.checkState() == Qt.PartiallyChecked:
                if pkg.installed == Qt.Unchecked:
                    TVModel.add_item_to_section('tobeinstalled', pkg)
                if pkg.installed == Qt.Checked:
                    TVModel.add_item_to_section('tobeuninstalled', pkg)
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            pkg.installed = item.checkState()

            # make sure the following is done when pkg is uninstalled
            # kfconf.cfg['installed'][pkg.ppa].pop(pkg.id)
            # TVModel.delete_ppa_if_empty('installed', pkg.ppa)

    @staticmethod
    def delete_ppa_if_empty(section, ppa):
        if not kfconf.cfg[section][ppa]:
            kfconf.cfg[section].pop(ppa)

    @staticmethod
    def add_item_to_section(section, pkg):
        if pkg.ppa not in kfconf.cfg[section]:
            kfconf.cfg[section][pkg.ppa] = {}
        if pkg.id not in kfconf.cfg[section][pkg.ppa]:
            kfconf.cfg[section][pkg.ppa][pkg.id] = {}
            kfconf.cfg[section][pkg.ppa][pkg.id]['name'] = pkg.name
            kfconf.cfg[section][pkg.ppa][pkg.id]['version'] = pkg.version
            kfconf.cfg[section][pkg.ppa][pkg.id]['deb_link'] = pkg.deb_link
            kfconf.cfg[section][pkg.ppa][pkg.id]['build_link'] = pkg.build_link
            kfconf.cfg[section][pkg.ppa][pkg.id]['deb_link'] = pkg.deb_link

    def install_btn_clicked(self):
        # uninstall packages that need uninstalling first.
        # self.uninstall_pkgs()
        # install packages that need installing
        self.install_pkgs()
        # TODO status bar progress report

    def uninstall_pkgs(self):
        # get list of packages to be uninstalled from cfg, using pop to delete
        for ppa in kfconf.cfg['tobeuninstalled']:
            for pkg in kfconf.cfg['tobeuninstalled'][ppa]:
                subprocess.run(['pkexec', './uninstall_pkg', pkg.binary_name], stdout=subprocess.PIPE)
                # TODO if success!!
                kfconf.cfg['installed'][pkg.ppa].pop(pkg.id)
                TVModel.delete_ppa_if_empty('installed', pkg.ppa)
        kfconf.cfg['tobeuninstalled'].clear()

    def install_pkgs(self):
        # get list of packages to be installed from cfg, using pop to delete
        for ppa in kfconf.cfg['tobeinstalled']:
            for pkg in kfconf.cfg['tobeinstalled'][ppa]:
                # self.download_debs(pkg)
                self.__result = self.__pool.apply_async(self.__packages._get_deb_links_,
                                                        (ppa, kfconf.cfg['tobeinstalled'][ppa][pkg]['build_link'].rsplit('/', 1)[-1], ),
                                                        callback=self.download_debs)
        kfconf.cfg['tobeinstalled'].clear()

    def download_debs(self, pkg):

        pass

    def convert_debs_to_rpms(self):
        pass

    def install_rpms(self, pkg):
        subprocess.run(['pkexec', './install_pkg', pkg.rpm_file], stdout=subprocess.PIPE)
