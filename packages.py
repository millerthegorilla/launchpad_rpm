#    This file is part of rpm_maker.

#    rpm_maker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    rpm_maker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

from pathlib import Path
import logging
import os
import re
import subprocess
import time
import uuid
from multiprocessing import Pool as mp_pool
from multiprocessing.dummy import Pool as thread_pool
from os.path import isfile, basename
from threading import RLock
from fuzzywuzzy import fuzz

import requests
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QGuiApplication
from bs4 import BeautifulSoup
from launchpadlib.errors import HTTPError
from launchpadlib.launchpad import Launchpad

from kfconf import cfg, cache, pkg_states, tmp_dir, \
                    clean_section, debs_dir, \
                    add_item_to_section, delete_ppa_if_empty
from download_process import DownloadProcess
from conversion_process import ConversionProcess
from installation_process import InstallationProcess
try:
    import rpm
except ImportError as e:
    try:
        import apt
    except ImportError as ee:
        raise Exception(str(e.args) + " : " + str(ee.args))


# TODO log messages are being written twice.
# TODO why is it stopping?


class Packages(QThread):
    download_finished_signal = pyqtSignal('PyQt_PyObject')
    conversion_finished_signal = pyqtSignal(bool)
    actioning_finished_signal = pyqtSignal()

    def __init__(self, team, arch,
                 msg_signal, log_signal, progress_signal,
                 transaction_progress_signal,
                 lock_model_signal, list_filling_signal,
                 cancel_signal, request_action_signal,
                 list_filled_signal):
        super().__init__()
        self.team = team
        self._launchpad = None
        self.arch = arch
        self._lp_ppa = None
        self._lp_team = None
        self._ppa = ''
        self._pkgs = []
        self.deb_paths_list = []
        self._thread_pool = thread_pool(10)
        self._mp_pool = mp_pool(10)
        self._result = None
        self.deb_links = None
        self.cancel_process = False
        self.installing = False

        # signals from above
        self.msg_signal = msg_signal
        self.log_signal = log_signal
        self.progress_signal = progress_signal
        self.transaction_progress_signal = transaction_progress_signal
        self.lock_model_signal = lock_model_signal
        self.list_filling_signal = list_filling_signal
        self.cancel_signal = cancel_signal
        self.request_action_signal = request_action_signal
        self.list_filled_signal = list_filled_signal

        # local signals
        self.download_finished_signal.connect(self.append_deb_links_and_convert)
        self.conversion_finished_signal.connect(self.continue_actioning)
        self.actioning_finished_signal.connect(self.finish_actioning)
        self.lock = RLock()
        self._total_length = 0
        self._current_length = 0

        # process handle for the sake of cancelling
        self.process = None

    def connect(self):
        self._launchpad = Launchpad.login_anonymously('kxfed.py', 'production')
        self._lp_team = self._launchpad.people[self.team]

    @property
    def lp_team(self):
        return self._lp_team

    @property
    def ppa(self):
        return self._ppa

    @ppa.setter
    def ppa(self, ppa):
        self._ppa = ppa

    @property
    def pkgs(self):
        return self._pkgs

    def populate_pkgs(self, ppa, arch):
        self.list_filling_signal.emit()
        self._thread_pool.apply_async(self.populate_pkg_list, (ppa, arch,),
                                      callback=self.list_filled_signal.emit)

    @cache.cache_on_arguments()
    def populate_pkg_list(self, ppa, arch):
        try:
            pkgs = []
            ubuntu = self._launchpad.distributions["ubuntu"]
            lp_ppa = self._lp_team.getPPAByName(distribution=ubuntu, name=ppa)

            ds1 = ubuntu.getSeries(name_or_version="trusty")
            ds2 = ubuntu.getSeries(name_or_version="lucid")
            ds3 = ubuntu.getSeries(name_or_version="xenial")
            ds4 = ubuntu.getSeries(name_or_version="bionic")

            d_s = [ds1, ds2, ds3, ds4]
            d_a_s = []
            for i in d_s:
                d_a_s.append(i.getDistroArchSeries(archtag=arch))
            p_b_h = []
            for i in d_a_s:
                p_b_h.append(lp_ppa.getPublishedBinaries(order_by_date=True, pocket="Release", status="Published",
                                                         distro_arch_series=i))
            for b in p_b_h:
                if len(b):
                    for i in b:
                        pkg = [i.build_link,
                               ppa,
                               i.binary_package_name,
                               i.binary_package_version,
                               uuid.uuid4().urn]
                        if pkg not in pkgs:
                            pkgs.append(pkg)

            cfg['cache']['initiated'] = time.time()
            return pkgs
        except HTTPError as http_error:
            self.log_signal.emit(http_error, logging.CRITICAL)

    @staticmethod
    def pkg_search(sections, search_value):
        """sections is a list of strings - names of sections - to search
           search value is content string"""
        for section in sections:
            for ppa in pkg_states[section]:
                for pkgid in pkg_states[section][ppa]:
                    if search_value in pkg_states[section][ppa][pkgid].dict().values():
                        return pkg_states[section][ppa][pkgid]
        return False

    def install_pkgs_button(self):
        try:
            ts = rpm.TransactionSet()
            if ts.dbMatch('name', 'python3-rpm').count() == 1:
                cfg['distro_type'] = 'rpm'
        except Exception as e:
            cfg['distro_type'] = 'deb'
        # TODO NOTICE - the following code can be refactored to use a function, I think
        clean_section(pkg_states['downloading'])
        if bool(pkg_states['downloading']):
            for ppa in pkg_states['downloading']:
                for pkgid in pkg_states['downloading'][ppa]:
                    if isfile(pkg_states['downloading'][ppa][pkgid]['rpm_path']):
                        add_item_to_section('installing', pkg_states['downloading'][ppa].pop(pkgid))
                    elif isfile(pkg_states['downloading'][ppa][pkgid]['deb_path']):
                        add_item_to_section('converting', pkg_states['downloading'][ppa].pop(pkgid))
                    else:
                        add_item_to_section('tobeinstalled', pkg_states['downloading'][ppa].pop(pkgid))
        clean_section(pkg_states['converting'])
        if bool(pkg_states['converting']):
            for ppa in pkg_states['converting']:
                for pkgid in pkg_states['converting'][ppa]:
                    if isfile(pkg_states['converting'][ppa][pkgid]['rpm_path']):
                        add_item_to_section('installing', pkg_states['converting'][ppa].pop(pkgid))
                    elif pkg_states['converting'][ppa][pkgid]['deb_path']:
                        if isfile(pkg_states['converting'][ppa][pkgid]['deb_path']):
                            self.deb_paths_list.append(pkg_states['converting'][ppa][pkgid]['deb_path'])
                        else:
                            add_item_to_section('tobeinstalled', pkg_states['converting'][ppa].pop(pkgid))
        clean_section(pkg_states['installing'])
        if bool(pkg_states['installing']):
            for ppa in pkg_states['installing']:
                for pkgid in pkg_states['installing'][ppa]:
                    if pkg_states['installing'][ppa][pkgid]['rpm_path']:
                        if isfile(pkg_states['installing'][ppa][pkgid]['rpm_path']):
                            if pkg_states['installed'][ppa]:
                                if pkg_states['installed'][ppa][pkgid]:
                                    continue
                        elif isfile(pkg_states['installing'][ppa][pkgid]['deb_path']):
                            self.deb_paths_list.append(pkg_states['installing'][ppa][pkgid]['deb_path'])
                            add_item_to_section('converting', pkg_states['installing'][ppa].pop(pkgid))
                        else:
                            add_item_to_section('tobeinstalled', pkg_states['installing'][ppa].pop(pkgid))
        clean_section(pkg_states['uninstalling'])
        if bool(pkg_states['uninstalling']):
            for ppa in pkg_states['uninstalling']:
                for pkgid in pkg_states['uninstalling'][ppa]:
                    ts = rpm.TransactionSet()
                    if not len(ts.dbMatch('name', pkg_states['uninstalling'][ppa][pkgid]['name'])):
                        self.msg_signal.emit("there is an error in the cache. ",
                                             pkg_states['uninstalling'][ppa][pkgid]['name'],
                                             "is not installed.")
                        self.log_signal.emit("there is an error in the cache. ",
                                             pkg_states['uninstalling'][ppa][pkgid]['name'],
                                             "is not installed.  Find the cache section in the config file,"
                                             " at USERHOME/.config/kxfed/kxfed.cfg",
                                             " and delete the package from the uninstalling section.")
        pkg_processes = [DownloadProcess(team_link=self.lp_team.web_link,
                                         msg_signal=self.msg_signal,
                                         log_signal=self.log_signal,
                                         progress_signal=self.progress_signal),
                         ConversionProcess(msg_signal=self.msg_signal,
                                           log_signal=self.log_signal,
                                           progress_signal=self.progress_signal),
                         InstallationProcess(msg_signal=self.msg_signal,
                                             log_signal=self.log_signal,
                                             progress_signal=self.progress_signal,
                                             transaction_progress_signal=self.transaction_progress_signal,
                                             request_action_signal=self.request_action_signal)]
        for pkg_process in pkg_processes:
            pkg_process.read_section()
            pkg_process.state_change()
            pkg_process.move_cache()

        # self.deb_paths_list = []
        # try:
        #     ts = rpm.TransactionSet()
        #     if ts.dbMatch('name', 'python3-rpm').count() == 1:
        #         cfg['distro_type'] = 'rpm'
        # except Exception as e:
        #     cfg['distro_type'] = 'deb'
        # # TODO NOTICE - the following code requires delete_ppa_if_empty to be used at all times
        # # TODO ie if bool(pkg_states['tobeinstalled']): hence the 'clean_section' which removes dangling ppas
        # clean_section(pkg_states['downloading'])
        # if bool(pkg_states['downloading']):
        #     for ppa in pkg_states['downloading']:
        #         for pkgid in pkg_states['downloading'][ppa]:
        #             if isfile(pkg_states['downloading'][ppa][pkgid]['rpm_path']):
        #                 add_item_to_section('installing', pkg_states['downloading'][ppa].pop(pkgid))
        #             elif isfile(pkg_states['downloading'][ppa][pkgid]['deb_path']):
        #                 add_item_to_section('converting', pkg_states['downloading'][ppa].pop(pkgid))
        #             else:
        #                 add_item_to_section('tobeinstalled', pkg_states['downloading'][ppa].pop(pkgid))
        # clean_section(pkg_states['converting'])
        # if bool(pkg_states['converting']):
        #     for ppa in pkg_states['converting']:
        #         for pkgid in pkg_states['converting'][ppa]:
        #             if isfile(pkg_states['converting'][ppa][pkgid]['rpm_path']):
        #                 add_item_to_section('installing', pkg_states['converting'][ppa].pop(pkgid))
        #             elif pkg_states['converting'][ppa][pkgid]['deb_path']:
        #                 if isfile(pkg_states['converting'][ppa][pkgid]['deb_path']):
        #                     self.deb_paths_list.append(pkg_states['converting'][ppa][pkgid]['deb_path'])
        #                 else:
        #                     add_item_to_section('tobeinstalled', pkg_states['converting'][ppa].pop(pkgid))
        # clean_section(pkg_states['installing'])
        # if bool(pkg_states['installing']):
        #     for ppa in pkg_states['installing']:
        #         for pkgid in pkg_states['installing'][ppa]:
        #             if pkg_states['installing'][ppa][pkgid]['rpm_path']:
        #                 if isfile(pkg_states['installing'][ppa][pkgid]['rpm_path']):
        #                     if pkg_states['installed'][ppa]:
        #                         if pkg_states['installed'][ppa][pkgid]:
        #                             continue
        #                 elif isfile(pkg_states['installing'][ppa][pkgid]['deb_path']):
        #                     self.deb_paths_list.append(pkg_states['installing'][ppa][pkgid]['deb_path'])
        #                     add_item_to_section('converting', pkg_states['installing'][ppa].pop(pkgid))
        #                 else:
        #                     add_item_to_section('tobeinstalled', pkg_states['installing'][ppa].pop(pkgid))
        # clean_section(pkg_states['uninstalling'])
        # if bool(pkg_states['uninstalling']):
        #     for ppa in pkg_states['uninstalling']:
        #         for pkgid in pkg_states['uninstalling'][ppa]:
        #             ts = rpm.TransactionSet()
        #             if not len(ts.dbMatch('name', pkg_states['uninstalling'][ppa][pkgid]['name'])):
        #                 self.msg_signal.emit("there is an error in the cache. ",
        #                                      pkg_states['uninstalling'][ppa][pkgid]['name'],
        #                                      "is not installed.")
        #                 self.log_signal.emit("there is an error in the cache. ",
        #                                      pkg_states['uninstalling'][ppa][pkgid]['name'],
        #                                      "is not installed.  Find the cache section in the config file,"
        #                                      " at USERHOME/.config/kxfed/kxfed.cfg",
        #                                      " and delete the package from the uninstalling section.")
        # # start install process by downloading packages
        # if bool(pkg_states['tobeinstalled']):
        #     if cfg['download'] == 'True':
        #         self._thread_pool.apply_async(self.download_packages, callback=self.download_finished_signal.emit)
        # elif cfg['convert'] == 'True':
        #     if self.deb_paths_list:
        #         self.continue_convert(self.deb_paths_list)
        #
        # if cfg['install'] == 'True' or cfg['uninstall'] == 'True':
        #     if bool(pkg_states['installing']) or bool(pkg_states['uninstalling']):
        #         self.continue_actioning(True)

    def cancel(self):
        self.cancel_process = True
        if self.process is not None:
            self.process.stdin.write(b"cancel")
            self.process.terminate()
        self.cancel_signal.emit()

    def download_packages(self, deb_paths=None):
        # get list of packages to be installed from cfg, using pop to delete
        self.log_signal.emit('Downloading Packages', logging.INFO)
        self.progress_signal.emit(0, 0)
        deb_links = []
        if deb_paths:
            deb_links = deb_links + deb_paths
        pkg_states['downloading'] = {}

        for ppa in pkg_states['tobeinstalled']:
            for pkgid in pkg_states['tobeinstalled'][ppa]:
                pkg = pkg_states['tobeinstalled'][ppa].pop(pkgid)
                # some housekeeping?
                if ppa in pkg_states['installing']:
                    if pkgid in pkg_states['installing'][ppa] and\
                            pkg_states['installing'][ppa][pkgid]['rpm_path']:
                        if isfile(pkg_states['installing'][ppa][pkgid]['rpm_path']):
                            break
                        else:
                            pkg_states['installing'][ppa][pkgid]['rpm_path'] = ''
                            add_item_to_section('tobeinstalled', pkg_states['installing'][ppa].pop(pkgid))
                if ppa in pkg_states['installed']:
                    # needed because there are sometimes the same package in different ppas
                    if pkgid in pkg_states['installed'][ppa]:
                        self.msg_signal.emit(pkg['name'] + " is already installed")
                        self.log_signal.emit(pkg['name'] + " is already installed")
                        break
                clean_section(pkg_states['downloading'])
                if ppa not in pkg_states['downloading']:
                    pkg_states['downloading'][ppa] = {}
                cfg.write()
                paths = list(Path(debs_dir).glob(pkg['name'] + '*'))
                if paths and fuzz.token_set_ratio(pkg['version'],
                                                  basename(str(paths[0]).
                                                  replace(pkg['name'] + '_', '')).
                                                  rsplit('_', 1)[0]) > 90:
                    self.msg_signal.emit('Package' +
                                         pkg['name'] +
                                         'has already been downloaded, moving to conversion list')
                    self.log_signal.emit('Package' +
                                         pkg['name'] +
                                         'has already been downloaded, moving to conversion list',
                                         logging.INFO)
                    pkg['deb_path'] = str(paths[0])
                    add_item_to_section('converting', pkg)
                    cfg.write()
                    continue
                pkg_states['downloading'][ppa][pkgid] = pkg
                if isfile(pkg_states['downloading'][ppa][pkgid]['deb_path']):
                    deb_links.append(pkg_states['downloading'][ppa][pkgid]['deb_path'])
                else:
                    result = self._thread_pool.apply_async(self.get_deb_link_and_download,
                                                           (ppa,
                                                            pkg,
                                                            debs_dir,
                                                            self.lp_team.web_link,))
                    deb_links.append(result.get())
                self._total_length = 0
                self._current_length = 0
        return deb_links

    def get_deb_link_and_download(self, ppa, pkg, debs_dir, web_link):
        # threaded function - gets build link from page and then parses that link
        # to obtain the download links for the package, downloads the package
        # and returns a path for the package deb file.
        try:
            html = requests.get(web_link
                                + '/+archive/ubuntu/'
                                + ppa
                                + '/+build/' + pkg['build_link'].rsplit('/', 1)[-1])
            links = BeautifulSoup(html.content, 'lxml').find_all('a',
                                                                 href=re.compile(r''
                                                                                 + pkg['name']
                                                                                 + '(.*?)(all|amd64\.deb)'))
            assert len(links) == 1
            pkg['deb_link'] = links[0]
            link = links[0]
            # deb_paths = []
            # for link in links:
            fn = link['href'].rsplit('/', 1)[-1]
            fp = debs_dir + fn
            if not isfile(fp):
                self.log_signal.emit("Downloading " + pkg['name'] + ' from ' + str(link['href']), logging.INFO)
                self.msg_signal.emit("Downloading " + pkg['name'])
                with open(fp, "wb+") as f:
                    response = requests.get(link['href'], stream=True)
                    total_length = response.headers.get('content-length')
                    if total_length is None:  # no content length header
                        f.write(response.content)
                    else:
                        self.lock.acquire()
                        self._total_length += int(total_length)
                        self.lock.release()

                        for data in response.iter_content(chunk_size=1024):
                            f.write(data)
                            self.lock.acquire()
                            self._current_length += len(data)
                            self.progress_signal.emit(self._current_length, self._total_length)
                            self.lock.release()
                # deb_paths.append(fp)
            pkg['deb_path'] = fp
            cfg.write()
            return fp
        except requests.HTTPError as e:
            self.log_signal.emit(e, logging.CRITICAL)

    @pyqtSlot('PyQt_PyObject')
    def append_deb_links_and_convert(self, deb_paths_list):
        """
        A bound method that is called by self.download_finished_signal
        in case extra packages have been downloaded after some others
        :type deb_paths_list: object
        """
        if deb_paths_list:
            self.deb_paths_list = self.deb_paths_list + deb_paths_list
        self.continue_convert(self.deb_paths_list)

    def continue_convert(self, deb_paths_list):
        """
        A method that wraps a thread_pool.apply_async call to allow the
        user to maintain access to the gui whilst packages are converted.
        Conversion_finished_signal is emitted when the apply_async
        method is done.
        :param deb_paths_list:
        :type deb_paths_list:
        :return: none
        :rtype: none
        """
        # async call convert function allows access to gui to continue
        if self.cancel_process:
            self.conversion_finished_signal.emit(False)
        if deb_paths_list:
            if cfg['convert'] == 'True' and cfg['distro_type'] == 'rpm':
                self.lock_model_signal.emit(True)
                self._thread_pool = thread_pool(10)
                self.log_signal.emit('Converting packages : ' + str(deb_paths_list), logging.INFO)
                self.msg_signal.emit('Converting Packages...')

                result = self._thread_pool.apply_async(self.convert_packages,
                                                       (deb_paths_list,),
                                                       callback=self.conversion_finished_signal.emit)
                #self.conversion_finished_signal.emit(result.get())

    # TODO this needs to be refactored.  the loop for deb_path at 395 is inefficient.
    # TODO I'm sure I can rewrite with isfile(path), or similar.
    # TODO also all functions, ie download, convert, install, should be classes
    # TODO with the appropriate process internal, so that they can be disposed of
    # TODO safely, for memory management.  Once that is the case, then each class can
    # TODO handle the positioning of the package in the config's cache.
    def convert_packages(self, deb_path_list):
        if self.cancel_process is True:
            return False
        self.progress_signal.emit(0, len(deb_path_list))  # ?
        deb_pkgs = []
        for file_path in deb_path_list:
            deb_pkgs.append(file_path)
        for deb_path in deb_pkgs:
            for ppa in pkg_states['downloading']:
                for pkg_id in pkg_states['downloading'][ppa]:
                    tag = pkg_states['downloading'][ppa][pkg_id]['deb_link']
                    if os.path.basename(deb_path) == str(tag.contents[0]):
                        pkg = pkg_states['downloading'][ppa].pop(pkg_id)
                        if ppa not in pkg_states['converting']:
                            pkg_states['converting'][ppa] = {}
                        pkg_states['converting'][ppa][pkg_id] = pkg
        pkg_states['downloading'] = {}

        cfg.write()
        if self.cancel_process is True:
            return False
        from getpass import getuser
        username = getuser()
        del getuser
        try:
            self.process = subprocess.Popen(['pkexec', '/home/james/Src/kxfed/build_rpms.sh', username,
                                             cfg['rpms_dir'], cfg['arch']] + deb_pkgs,
                                            bufsize=1,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        except Exception as e:
            self.log_signal.emit(e)
        conv = False
        num_of_conv = 0
        while 1:
            if self.cancel_process:
                return False
            QGuiApplication.instance().processEvents()
            nextline = self.process.stdout.readline().decode('utf-8')
            self.process.stdout.flush()
            self.log_signal.emit(nextline, logging.INFO)
            if 'Converted' in nextline:
                word_list = nextline.split(' to ')
                rpm_name = word_list[1].rstrip('\n')
                deb_path = word_list[0].lstrip('Converted ')
                found_pkg = self.pkg_search(['converting'], search_value=deb_path)
                if found_pkg:
                    if not pkg_states['installing']:
                        pkg_states['installing'] = {}
                    if found_pkg.parent.name not in pkg_states['installing']:
                        pkg_states['installing'][found_pkg.parent.name] = {}
                    pkg_states['installing'][found_pkg.parent.name][found_pkg.name] = \
                        pkg_states['converting'][found_pkg.parent.name].pop(found_pkg.name)
                    pkg_states['installing'][found_pkg.parent.name][found_pkg.name]['rpm_path'] = \
                        cfg['rpms_dir'] + rpm_name
                    conv = True
                    num_of_conv += 1
                    if os.path.exists(found_pkg['deb_path']) and cfg['delete_downloaded'] == 'True':
                        os.remove(found_pkg['deb_path'])
                    self.progress_signal.emit(num_of_conv, len(deb_pkgs))
                    self.msg_signal.emit(nextline)
                else:
                    conv = False
            if nextline == '' and self.process.poll() is not None:
                break
        if conv is True:
            cfg.filename = (cfg['config']['dir'] + cfg['config']['filename'])
            cfg.write()
            for ppa in pkg_states['converting']:
                if pkg_states['converting'][ppa]:
                    for pkg in pkg_states['converting'][ppa]:
                        self.log_signal.emit('Error - did not convert ' + str(pkg.name), logging.INFO)
            pkg_states['converting'] = {}
        else:
            self.log_signal.emit(Exception("There is an error with the bash script when converting."), logging.CRITICAL)
            return False
        return True

    @pyqtSlot(bool)
    def continue_actioning(self, param):
        reconvert_list = []
        if param is not True or self.cancel_process is True:
            return
        # param is boolean, returned from converting_packages for the sake of result.get()
        if cfg['install'] == 'True' or cfg['uninstall'] == 'True':
            clean_section(pkg_states['installing'])
            clean_section(pkg_states['uninstalling'])
            if pkg_states['installing'] or pkg_states['uninstalling']:
                self.log_signal.emit("Actioning packages...", logging.INFO)
                self.msg_signal.emit("Actioning packages...")
                install_msg_txt = ""
                uninstall_msg_txt = ""
                msg_txt = ""
                for ppa in pkg_states['installing']:
                    for pkg in pkg_states['installing'][ppa]:
                        if isfile(pkg_states['installing'][ppa][pkg]['rpm_path']):
                            install_msg_txt += pkg_states['installing'][ppa][pkg]['name'] + "\n"
                        else:
                            reconvert_list.append(pkg_states['installing'][ppa][pkg])
                            pkg_states['installing'][ppa].pop(pkg)
                    delete_ppa_if_empty('installing', ppa)
                for ppa in pkg_states['uninstalling']:
                    for pkg in pkg_states['uninstalling'][ppa]:
                        uninstall_msg_txt += pkg_states['uninstalling'][ppa][pkg]['name'] + "\n"
                if reconvert_list:
                    self.msg_signal.emit("Some packages failed to convert - Reconverting")
                    self.log_signal.emit("Some packages failed to convert - Reconverting", logging.INFO)
                    deb_paths_list = []
                    clean_section(pkg_states['tobeinstalled'])
                    for pkg in reconvert_list:
                        if pkg['deb_path'] and isfile(pkg['deb_path']):
                            deb_paths_list.append(pkg['deb_path'])
                        else:
                            pkg['deb_path'] = ''
                            add_item_to_section('tobeinstalled', pkg)
                    self._thread_pool.apply_async(self.download_packages,
                                                  (deb_paths_list,),
                                                  callback=self.download_finished_signal.emit)
                else:
                    if install_msg_txt:
                        msg_txt = "This will install: \n" + install_msg_txt
                        if uninstall_msg_txt:
                            msg_txt += "\n and will uninstall: \n" + uninstall_msg_txt
                    elif uninstall_msg_txt:
                        msg_txt = "This will uninstall: \n" + uninstall_msg_txt
                    self.request_action_signal.emit(msg_txt)

    def continue_actioning_if_ok(self):
        if self.cancel_process is True:
            return
        self.lock_model_signal.emit(True)
        self._thread_pool = thread_pool(10)

        if cfg['distro_type'] == 'rpm':
            self._thread_pool.apply_async(self._action_rpms, callback=self.actioning_finished_signal.emit)
        else:
            self._install_debs()

    @pyqtSlot()
    def finish_actioning(self):
        self.lock_model_signal.emit(False)

    def _action_rpms(self):
        if self.cancel_process:
            return
        rpm_links = []
        for ppa in pkg_states['installing']:
            for pkg in pkg_states['installing'][ppa]:
                if isfile(pkg_states['installing'][ppa][pkg]['rpm_path']):
                    rpm_links.append(pkg_states['installing'][ppa][pkg]['rpm_path'])
        for ppa in pkg_states['uninstalling']:
            for pkg in pkg_states['uninstalling'][ppa]:
                rpm_links.append('uninstalling' + pkg_states['uninstalling'][ppa][pkg]['name'])
        try:
            if rpm_links:
                self.process = subprocess.Popen(['pkexec',
                                                 '/home/james/Src/kxfed/dnf_install.py',
                                                 tmp_dir] + rpm_links,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
            else:
                raise ValueError("Error! : rpm_paths of packages in cache may be empty")
        except Exception as e:
            self.log_signal.emit(e, logging.CRITICAL)

        while 1:
            if self.cancel_process:
                return
            QGuiApplication.instance().processEvents()
            line = self.process.stdout.readline().decode('utf-8')
            self.process.stdout.flush()
            if line:
                # self.log_signal.emit(line, logging.INFO)
                if 'kxfedlog' in line:
                    self.log_signal.emit(line.lstrip('kxfedlog'), logging.INFO)
                elif 'kxfedexcept' in line:
                    self.log_signal.emit(line.lstrip('kxfedexcept'), logging.CRITICAL)
                    self.msg_signal.emit('Error Installing! Check messages...')
                elif 'kxfedmsg' in line:
                    self.msg_signal.emit(line.lstrip('kxfedmsg'))
                elif 'kxfedprogress' in line:
                    sig = line.split(' ')
                    self.progress_signal.emit(sig[1], sig[2])
                elif 'kxfedtransprogress' in line:
                    sig = line.split(' ')
                    if sig[1] == sig[2]:
                        self.msg_signal.emit('Verifying package, please wait...')
                    self.transaction_progress_signal.emit(sig[1], sig[2])
                elif 'kxfedinstalled' in line:
                    name = line.lstrip('kxfedinstalled').replace('\n', '').strip()
                    self.msg_signal.emit('Installed ' + name)
                    self.log_signal.emit('Installed ' + name, logging.INFO)
                    section = self.pkg_search(['installing'], name)
                    section.parent.pop(section['name'])
                    add_item_to_section('installed', section)
                    # TODO schedule check or callback to run rpm.db_match to check install ok
                elif 'kxfeduninstalled' in line:
                    name = line.lstrip('kxfeduninstalled').replace('\n', '').strip()
                    self.msg_signal.emit('Uninstalled ' + line.lstrip('kxfeduninstalled'))
                    self.log_signal.emit('Uninstalled ' + line.lstrip('kxfeduninstalled'))
                    section = self.pkg_search(['uninstalling'], name)
                    section.parent.pop(section['name'])
                # TODO delete package from uninstalled state
                # TODO change highlighted color of checkbox row to normal color
                # TODO delete rpm if it says so in the preferences
                elif 'kxfedstop' in line:
                    self.msg_signal.emit("Transaction ", line.lstrip('kxfedstop'), " has finished")
                    self.log_signal.emit("Transaction ", line.lstrip('kxfedstop'), " has finished")

                if line == '' and self.process.poll() is not None:
                    break

    # @pyqtSlot(int, QProcess.ExitStatus)
    # def catch_signal_install(self, exitcode, exitstatus):
    #     self.installing = False
    #     if exitcode != 0 | exitstatus != QProcess.NormalExit:
    #         self.log_signal.emit("error processing install_rpms", logging.ERROR)

    def _install_debs(self):
        pass
