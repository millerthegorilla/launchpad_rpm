#    This file is part of rpm_maker.

#    rpm_maker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    rpm_maker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with rpm_maker.  If not, see <https://www.gnu.org/licenses/>.
#    (c) 2018 - James Stewart Miller
from PyQt5.QtCore import pyqtSignal, QObject, QCoreApplication
from launchpadlib.launchpad import Launchpad
from launchpadlib.errors import HTTPError
from multiprocessing.dummy import Pool as thread_pool
from multiprocessing import Pool as mp_pool
from kfconf import cfg, cache, config_search
import requests
import subprocess
import os
from bs4 import BeautifulSoup
import re
import time
import logging

try:
    import rpm
except ImportError as e:
    try:
        import apt
    except ImportError as ee:
        raise Exception(e.args + " : " + ee.args)


class Packages(QObject):

    progress_adjusted = pyqtSignal(int, int, str)
    transaction_progress_adjusted = pyqtSignal(int, int)
    log = pyqtSignal('PyQt_PyObject', int)
    message_user = pyqtSignal(str)
    pkg_list_complete = pyqtSignal(list)
    cancelled = pyqtSignal()

    def __init__(self, team, arch):
        super().__init__()
        self.team = team
        self._launchpad = None
        self.arch = arch
        self._lp_ppa = None
        self._lp_team = None
        self._ppa = ''
        self._pkgs = []
        self.debs = []
        self._thread_pool = thread_pool(10)
        self._mp_pool = mp_pool(10)
        self._result = None
        self.deb_links = None
        self._rpmtsCallback_fd = None
        self.cancel_process = False

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
        self._thread_pool.apply_async(self.populate_pkg_list, (ppa, arch,), callback=self.pkg_list_complete.emit)

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
                               i.binary_package_version]
                        if pkg not in pkgs:
                            pkgs.append(pkg)
                            # self.populate_pkgs.set(lp_ppa + i.binary_package_name,
                            #                        pkg)
            # do I need to cache _pkgs in instance variable - why not use a local?
            # returns pkgs for sake of cache.
            return pkgs
        except HTTPError as http_error:
            self.log.emit(http_error, logging.CRITICAL)

    @staticmethod
    def uninstall_pkgs(self):
        # get list of packages to be uninstalled from cfg, using pop to delete
        for ppa in cfg['tobeuninstalled']:
            for pkg in cfg['tobeuninstalled'][ppa]:
                #subprocess.run(['pkexec', './uninstall_pkg', pkg.binary_name], stdout=subprocess.PIPE)
                # TODO if success!!
                cfg['installed'][pkg.ppa].pop(pkg.id)
                cfg.delete_ppa_if_empty('installed', pkg.ppa)
        cfg['tobeuninstalled'].clear()

    def install_pkgs_button(self):
        try:
            ts = rpm.TransactionSet()
            if ts.dbMatch('name', 'python3-rpm').count() == 1:
                cfg['distro_type'] = 'rpm'
        except Exception as e:
            cfg['distro_type'] = 'deb'
        if cfg['download'] == 'True':
            deb_paths = self.download_packages()
        # a new function is required in order for QT to resolve the
        # dependency graph successfully, due to the multithreading
        # lots of hassle with threading and signals
        result = self.continue_convert(deb_paths)
        # while result.ready() is False:
        #
        #
        if result.get() is True:
            QCoreApplication.instance().processEvents()
            self._thread_pool.apply_async(self.finished_converting)

    def finished_converting(self):
        self.message_user.emit('Finished Converting Packages')
        self.log.emit('Finished Converting Packages', logging.INFO)
        time.sleep(1)
        self.continue_install()

    def continue_convert(self, deb_paths):
        # async call convert function allows access to gui to continue
        if cfg['convert'] == 'True' and cfg['distro_type'] == 'rpm':
            self._thread_pool = thread_pool(10)
            result = self._thread_pool.apply_async(self.convert_packages,
                                                   (deb_paths,))
            return result

    def continue_install(self):
        if cfg['install'] == 'True':
            if cfg['distro_type'] == 'rpm':
                self._thread_pool.apply_async(self._install_rpms)
            else:
                self._install_debs()

    def download_packages(self):
        # get list of packages to be installed from cfg, using pop to delete
        self.log.emit('Downloading Packages', logging.INFO)
        self.progress_adjusted.emit(0, 0, "")
        deb_links = []
        cfg['downloading'] = {}

        for ppa in cfg['tobeinstalled']:

            for pkgid in cfg['tobeinstalled'][ppa]:
                if ppa not in cfg['installing'] and ppa not in cfg['installed']:
                    pkg = cfg['tobeinstalled'][ppa].pop(pkgid)
                    if ppa not in cfg['downloading']:
                        cfg['downloading'][ppa] = {}
                    cfg['downloading'][ppa][pkgid] = pkg
                    cfg.write()
                    debs_dir = cfg['debs_dir']
                    self.message_user.emit("Downloading " + pkg.get('name'))
                    result = self._thread_pool.apply_async(self.get_deb_links_and_download,
                                                           (ppa,
                                                            pkg,
                                                            debs_dir,
                                                            self.lp_team.web_link,))
                    deb_links.append(result.get())
        return deb_links

    def get_deb_links_and_download(self, ppa, pkg, debs_dir, web_link):
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
            pkg['deb_link'] = links
            deb_paths = []
            self.log.emit("Downloading " + pkg.name + ' from ' + str(links), logging.INFO)
            for link in links:
                fn = link['href'].rsplit('/', 1)[-1]
                fp = debs_dir + fn
                with open(fp, "wb+") as f:
                    response = requests.get(link['href'], stream=True)
                    total_length = response.headers.get('content-length')

                    if total_length is None:  # no content length header
                        f.write(response.content)
                    else:
                        total_length = int(total_length)
                        for data in response.iter_content(chunk_size=1024):
                            f.write(data)
                            self.progress_adjusted.emit(len(data), total_length, "")
                            total_length = 0
                deb_paths.append(fp)
            pkg['deb_paths'] = deb_paths
            return deb_paths
        except requests.HTTPError as e:
            self.log.emit(e, logging.CRITICAL)

    def convert_packages(self, deb_paths):
        self.log.emit('Converting packages : ' + str(deb_paths), logging.INFO)
        self.progress_adjusted.emit(0, 0, "")
        deb_pkgs = []
        for deb_list in deb_paths:
            for filepath in deb_list:
                deb_pkgs.append(filepath)

        for deb in deb_pkgs:
            for ppa in cfg['downloading']:
                for pkgid in cfg['downloading'][ppa]:
                    tag = cfg['downloading'][ppa][pkgid]['deb_link'][0]
                    if os.path.basename(deb) == str(tag.contents[0]):
                        pkg = cfg['downloading'][ppa].pop(pkgid)
                        if ppa not in cfg['converting']:
                            cfg['converting'][ppa] = {}
                        cfg['converting'][ppa][pkgid] = pkg
        cfg['downloading'] = {}

        cfg.write()
        try:
            process = subprocess.Popen(['pkexec', '/home/james/Src/kxfed/build_rpms.sh', cfg['rpms_dir'], cfg['arch']] +
                                       deb_pkgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            self.log.emit(e)

        self.log.emit('Converting packages : ' + str(deb_pkgs), logging.INFO)
        conv = False
        while True:
            nextline = process.stdout.readline().decode('utf-8')
            self.log.emit(nextline, logging.INFO)
            if 'Converted' in nextline:
                # self.message_user.emit(nextline)
                cfg['converting'].walk(config_search, search_value=nextline[len('Converted '):nextline.index('_')])
                if cfg['found']:
                    if not cfg['installing']:
                        cfg['installing'] = {}
                    if cfg['found'].parent.name not in cfg['installing']:
                        cfg['installing'][cfg['found'].parent.name] = {}
                    cfg['installing'][cfg['found'].parent.name][cfg['found'].name] = \
                        cfg['converting'][cfg['found'].parent.name].pop(cfg['found'].name)
                    cfg['found'] = {}
                    conv = True
                    self.progress_adjusted.emit(round(100 / len(deb_pkgs)), 100, nextline)
                else:
                    conv = False
            if nextline == '' and process.poll() != None:
                break

        if conv is True:
            cfg.filename = (cfg['config']['dir'] + cfg['config']['filename'])
            cfg.write()
            for ppa in cfg['converting']:
                if cfg['converting'][ppa]:
                    for pkg in cfg['converting'][ppa]:
                        self.log.emit('Error - did not convert ' + str(pkg.name), logging.INFO)
            cfg['converting'] = {}
            return True
        else:
            self.log.emit(Exception("There is an error with the bash script when converting."), logging.CRITICAL)

    def _install_rpms(self):
        self.message_user.emit("Installing packages")
        ts = rpm.TransactionSet()
        for ppa in cfg['installing']:
            for pkg in cfg['installing'][ppa]:
                for path in pkg['deb_paths']:
                    h = rpm.readRpmHeader(ts, path)
                    ts.addInstall(h, path, 'u')
        unresolved_deps = ts.check()
        if unresolved_deps:
            self.log.emit("Unresolved Dependencies", logging.CRITICAL)
            for dep_failure in unresolved_deps:
                self.log.emit(str(dep_failure))
            self.message_user.emit("CRITICAL ERROR - packages have unmet dependencies, see messages")
        else:
            ts.order()
            self.log.emit("This will install: \n", logging.INFO)
            for te in ts:
                self.log.emit("%s-%s-%s" % (te.N(), te.V(), te.R()))
            ts.run(self.run_callback, ts)

    def run_callback(self, reason, amount, total, key, client_data=None):
        if self.cancelled:
            rpm.TransactionSet(client_data).clear()

        if reason == rpm.RPMCALLBACK_INST_OPEN_FILE:
            self.log.emit("Opening file. ", reason, amount, total, key, client_data)
            self._rpmtsCallback_fd = os.open(key, os.O_RDONLY)
            return self._rpmtsCallback_fd
        elif reason == rpm.RPMCALLBACK_INST_CLOSE_FILE:
            self.log.emit("Closing file. ", reason, amount, total, key, client_data)
            os.close(self._rpmtsCallback_fd)
        elif reason == rpm.RPMCALLBACK_INST_START:
            self.message_user.emit('Installing', key)
        elif reason == rpm.RPMCALLBACK_INST_PROGRESS:
            self.progress_adjusted.emit(amount, total, "")
            if amount == total:
                pass
                #cfg['installing'].walk()
        elif reason == rpm.RPMCALLBACK_TRANS_PROGRESS:
            self.transaction_progress_adjusted.emit(amount, total)
        elif reason == rpm.RPMCALLBACK_TRANS_STOP:
            self.transaction_progress_adjusted.emit(0,0)

    def _install_debs(self):
        pass
