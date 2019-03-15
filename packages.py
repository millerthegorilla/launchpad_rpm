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
from PyQt5.QtCore import pyqtSignal, QObject
from launchpadlib.launchpad import Launchpad
from launchpadlib.errors import HTTPError
import logging
import re
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as thread_pool
from multiprocessing import Pool as mp_pool
from kfconf import cfg, cache, config_search
import requests
import subprocess
import traceback
import threading
import os
import distro
try:
  import rpm
except ImportError as exc:
    if "exists" in str(exc):
        # is fedora/centos.
        pass
    else:
        # is not fedora
        raise


# TODO send exception data from stderror of rpm script and raise exception
# TODO and add pkg to cfg from exception_message in kxfed.py
# TODO and find out why the script is not working
# TODO and find out how to get the working directory in the correct place
# TODO and clean up the packages etc afterwards
# TODO and install, adding package details to list of installed packages.
# TODO then uninstall and preferences.
# TODO ** REMEMBER ** to selinux installed packages.
class Packages(QObject):

    progress_adjusted = pyqtSignal(int, int)
    progress_label = pyqtSignal(str)
    exception = pyqtSignal('PyQt_PyObject')
    message = pyqtSignal(str, int)
    pkg_list_complete = pyqtSignal(list)

    def __init__(self, team, arch):
        super().__init__()
        self._lp_team = team
        self._launchpad = None
        self._lp_arch = arch
        self._lp_ppa = None
        self._ppa = ''
        self._pkgs = []
        self.debs = []
        self._thread_pool = thread_pool(10)
        self._mp_pool = mp_pool(10)
        self._result = None
        self._lock = threading.Lock()

    def connect(self):
        self._launchpad = Launchpad.login_anonymously('kxfed.py', 'production')
        self._lp_team = self._launchpad.people[self._lp_team]

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

    def populate_pkgs(self, ppa):
        self._thread_pool.apply_async(self.populate_pkg_list, (ppa,), callback=self.pkg_list_complete.emit)

    @cache.cache_on_arguments()
    def populate_pkg_list(self, ppa):
        # ppa has to be passed in, for cache to work
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
                d_a_s.append(i.getDistroArchSeries(archtag=self._lp_arch))
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
            logging.log(logging.ERROR, str(http_error))

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

    def install_pkgs_signal_handler(self, label):
        self.progress_label.emit(label)

    def install_pkgs_button(self):
        if cfg['download'] == 'True':
            deb_links = self.download_packages()
        if cfg['convert'] == 'True' and 'Fedora' in distro.linux_distribution():
            self.convert_packages(deb_links)
        if cfg['install'] == 'True':
            try:
                ts = rpm.TransactionSet()
                if ts.dbMatch('name', 'python3-rpm').count() == 1:
                    self._install_rpms()
            except Exception as e:
                self._install_debs()

    def download_packages(self):
        # get list of packages to be installed from cfg, using pop to delete
        self.progress_label.emit('Downloading Packages')
        self.progress_adjusted.emit(0, 0)
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
                    result = self._thread_pool.apply_async(self._get_deb_links_and_download,
                                                           (ppa,
                                                            pkg,
                                                            debs_dir,))
                    deb_links.append(result.get())
        self._thread_pool.close()
        self._thread_pool.join()

        return deb_links

    def convert_packages(self, deb_links):

        deb_pkgs = []
        for deb_list in deb_links:
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

        process = subprocess.Popen(['pkexec', '/home/james/Src/kxfed/build_rpms.sh', cfg['rpms_dir'], cfg['arch']] +
                                   deb_pkgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #self.progress_adjusted.emit(0, 0)

        self.progress_label.emit('Converting packages')
        conv = False
        while True:
            conv = False
            nextline = process.stdout.readline().decode('utf-8')
            if 'Converted' in nextline:
                self.progress_label.emit(nextline)
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
            if nextline == '' and process.poll() != None:
                break
            self.progress_adjusted.emit(round(100 / len(deb_pkgs)), 100)

        # self.progress_adjusted.emit(0, 0)
        # self.progress_adjusted.emit(0, 100)
        if conv is True:
            self.progress_label.emit('Finished Converting Packages')
            for ppa in cfg['converting']:
                if ppa:
                    for pkg in ppa:
                        self.progress_label.emit('Error - did not convert ' + str(pkg.name))
            cfg['converting'] = {}
        else:
            raise Exception("There is an error with the bash script when converting.")

    def _get_deb_links_and_download(self, ppa, pkg, debs_dir):
        # threaded function called from install_packages
        try:
            html = requests.get(self._lp_team.web_link
                                + '/+archive/ubuntu/'
                                + ppa
                                + '/+build/' + pkg['build_link'].rsplit('/', 1)[-1])
            links = BeautifulSoup(html.content, 'lxml').find_all('a',
                                                                 href=re.compile(r''
                                                                                 + pkg['name']
                                                                                 + '(.*?)(all|amd64\.deb)'))
            pkg['deb_link'] = links
            deb_links = []
            for link in links:
                # TODO try os path basename etc out of interest
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
                            self.progress_adjusted.emit(len(data), total_length)
                            total_length = 0
                deb_links.append(fp)
            return deb_links
        except (requests.HTTPError, subprocess.CalledProcessError) as e:
            if e is subprocess.CalledProcessError:
                logging.log(logging.ERROR, e.output)
                self.exception.emit(e.stderror)
            else:
                logging.log(logging.ERROR, traceback.format_exc())
                self.exception.emit(e)

    def _install_rpms(self):
        pass
