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
from kfconf import cfg, cache
import requests
import subprocess
import traceback
import threading
import os
import sys
# import dbus
# import dbus.mainloop.glib
# import gi
# from gi.repository import GLib
# gi.require_version('Polkit', '1.0')
# from gi.repository import Polkit


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

    def __init__(self, team, arch):
        super().__init__()
        self._lp_team = team
        self._launchpad = None
        self._lp_arch = arch
        self._lp_ppa = ""
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
        pass

    @ppa.setter
    def ppa(self, ppa):
        self._lp_ppa = ppa

    @property
    def pkgs(self):
        return self._pkgs

    @cache.cache_on_arguments()
    def populate_pkgs(self, lp_ppa):
        try:
            pkgs = []
            ubuntu = self._launchpad.distributions["ubuntu"]
            ppa = self._lp_team.getPPAByName(distribution=ubuntu, name=lp_ppa)

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
                p_b_h.append(ppa.getPublishedBinaries(order_by_date=True, pocket="Release", status="Published",
                                                      distro_arch_series=i))
            for b in p_b_h:
                if len(b):
                    for i in b:
                        pkg = [i.build_link,
                               lp_ppa,
                               i.binary_package_name,
                               i.binary_package_version]
                        if pkg not in pkgs:
                            pkgs.append(pkg)
                            # self.populate_pkgs.set(lp_ppa + i.binary_package_name,
                            #                        pkg)
            # do I need to cache _pkgs in instance variable - why not use a local?
            return pkgs
        except HTTPError as http_error:
            logging.log(logging.ERROR, str(http_error))

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

    def install_pkgs(self):
        # get list of packages to be installed from cfg, using pop to delete
        self.progress_label.emit('Downloading Packages')
        tasks = []
        for ppa in cfg['tobeinstalled']:
            for pkgid in cfg['tobeinstalled'][ppa]:
                if ppa not in cfg['installing']:
                    cfg['downloading'][ppa] = {}
                pkg = cfg['tobeinstalled'][ppa].pop(pkgid)
                cfg['downloading'][ppa][pkgid] = pkg
                debs_dir = cfg['debs_dir']
                result = self._thread_pool.apply_async(self._get_deb_links_and_download,
                                              (ppa,
                                               pkg,
                                               debs_dir,))
                tasks.append(result.get())
        self._thread_pool.close()
        self._thread_pool.join()
        self.progress_adjusted.emit(0, 0)
        self.progress_label.emit('Converting Packages')
        deb_pkgs = ['pkexec', '/bin/bash', '/home/james/Src/kxfed/build_rpms.sh', cfg['rpms_dir'], cfg['arch']]
        for deb_list in tasks:
            for filepath in deb_list:
                deb_pkgs.append(filepath)

        process = subprocess.Popen(deb_pkgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while True:
            nextline = process.stdout.readline()
            if nextline == b'' and process.poll() != None:
                break
            if 'Wrote' in nextline.decode('utf-8'):
                self.progress_label.emit(nextline.decode('utf-8'))

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

    def _install_rpms(self, pkg):
        subprocess.run(['pkexec', './install_pkg', pkg.rpm_file], stdout=subprocess.PIPE)
