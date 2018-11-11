#!/usr/bin/env python

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QStandardItemModel
import multiprocessing.dummy
from packages import Packages
import subprocess
import kfconf
from kfconf import TVITEM_ROLE
from tvitem import TVItem
import requests
from datetime import datetime
from pathlib import Path
import logging

# TODO separate pkg downloading, converting and installing functions into
# TODO Packages class.  TVModel has reference to packages and Packages class
# TODO uses pyqtSignals to let the model know that it can update
# TODO that way the model can update when all packages are downloaded, handle
# TODO progressbar updates more efficiently etc. whilst keeping the implementation
# TODO details separate from the model, which is, effectively, the view.


class TVModel(QStandardItemModel):

    list_filled = pyqtSignal()
    progress_adjusted = pyqtSignal(int, int)
    message = pyqtSignal(str)

    def __init__(self, headers, team, arch, *args):
        # passing in conf to avoid static for threading.
        super().__init__(*args)
        try:
            self.__packages = Packages(team, arch)
        except Exception as e:
            logging.log(logging.ERROR, str(e))
            self.message.emit(str(e))
        # self.packages.get(self._setupModelData_) do this when ppa combo is selected
        self.setHorizontalHeaderLabels(headers)
        self.__pool = multiprocessing.dummy.Pool(10)
        self.__result = None
        self.itemChanged.connect(TVModel.on_item_changed)
        self._lock = multiprocessing.Lock()

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

    def action_pkgs(self):
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
                if ppa not in kfconf.cfg['installing']:
                    kfconf.cfg['downloading'][ppa] = {}
                kfconf.cfg['downloading'][ppa][pkg] = kfconf.cfg['tobeinstalled'][ppa].pop(pkg)
                self.__result = self.__pool.apply_async(self.__packages._get_deb_links_,
                                                        (ppa,
                                                         kfconf.cfg['downloading'][ppa][pkg]['build_link'],
                                                         kfconf.cfg['downloading'][ppa][pkg]['name'],),
                                                        callback=self.download_debs)
        kfconf.cfg['tobeinstalled'].clear()
        for ppa in kfconf.cfg['downloading']:
            for pkg in kfconf.cfg['downloading'][ppa]:
                for i in kfconf.cfg['downloading'][ppa][pkg]['deb_link']:
                    fn = i.rsplit('/', 1)[-1]
                    self.__pool.apply_async(self.download_file,
                                            (i, fn,),
                                            callback=self.downloads_finished)

    def download_debs(self, link_gen):
        # callback from packages._get_deb_links called by async_apply from
        # install_pkgs - multithreaded
        # practice configobj.walk, but can remove below and pass parameter around
        sect_list = []
        kfconf.cfg['downloading'].walk(self.config_search,
                                       call_on_sections=False,
                                       search_key=link_gen[0],
                                       sect=sect_list)
        section = sect_list.pop()
        section['deb_link'] = []
        self._lock.acquire()
        for i in link_gen[1]:
            section['deb_link'].append(i)
        self._lock.release()

    def convert_debs_to_rpms(self):
        for pkg in kfconf.cfg['converting']:
            self._lock.acquire()
            directory = kfconf.cfg['debs_dir'] + pkg['deb_link'][-1].rsplit('/', 1)[-1]
            filename = pkg['deb_link'][-1].rsplit('/', 1)[-1]
            rpms_dir = kfconf.cfg['rpms_dir']
            self._lock.release()
            try:
                result = subprocess.run(['build_rpms.sh',
                                         directory,
                                         directory + '/' + filename,
                                         rpms_dir,
                                         'amd64'],
                                        stdout=subprocess.PIPE).stdout.decode('utf-8')
            except Exception as e:
                logging.log(logging.ERROR, str(e))
            self._lock.acquire()
            kfconf['log'] += '\n' \
                             + 'Installing ' + filename \
                             + '\n' \
                             + datetime.now().strftime("%A, %d. %B %Y %I:%M%p %S seconds") \
                             + '\n' \
                             + result
            self._lock.release()

    def install_rpms(self, pkg):
        subprocess.run(['pkexec', './install_pkg', pkg.rpm_file], stdout=subprocess.PIPE)

    def download_file(self, url, file_name):
        # threaded function called from install_pkgs
        # using async_apply with a callback of downloads_finished
        self._lock.acquire()
        dn = kfconf.cfg['debs_dir'] + '/' + file_name
        fn = dn + '/' + file_name
        self._lock.release()
        try:
            if not Path(dn).exists():
                Path(dn).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logging.log(logging.ERROR, e.strerror)
            self.message(e.strerror)
        try:
            with open(fn, "wb+") as f:
                response = requests.get(url, stream=True)
                total_length = response.headers.get('content-length')

                if total_length is None:  # no content length header
                    f.write(response.content)
                else:
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=1024):
                        f.write(data)
                        self.progress_adjusted.emit(len(data), total_length)
                        total_length = 0
        except requests.HTTPError as e:
            logging.log(logging.Error, e.strerror)
            self.message(e.strerror)

        sect_list = []
        # try:
        #     self._lock.acquire()
        kfconf.cfg['downloading'].walk(self.config_search,
                                       search_key=url,
                                       call_on_sections=True,
                                       sect=sect_list)
            # if fn not in kfconf.cfg['converting']:
            #     kfconf.cfg['converting'][fn] = {}
            # bob = kfconf.cfg['downloading'].pop(sect_list[-1]).dict()
            # kfconf.cfg['converting'][fn] = bob
        #     self._lock.release()
        # except Exception as e:
        #     logging.log(logging.Error, e.strerror)

    def downloads_finished(self):
        self._lock.acquire()
        if not len(kfconf.cfg['downloading']):
            self.progress_adjusted.emit(0, 0)
            self.convert_debs_to_rpms()
        self._lock.release()

    def config_search(self, section, key, search_key, sect):
        if section[key] == search_key or search_key in section[key]:
            sect.append(section)
