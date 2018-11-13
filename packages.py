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
import multiprocessing.dummy
from kfconf import cfg, cache
import requests
import subprocess
import traceback


# TODO send exception data from stderror of rpm script and raise exception
# TODO and add pkg to cfg from exception_message in kxfed.py
# TODO and find out why the script is not working
# TODO and find out how to get the working directory in the correct place
# TODO and clean up the packages etc afterwards
# TODO and install, adding package details to list of installed packages.
# TODO then uninstall and preferences.
class Packages(QObject):

    progress_adjusted = pyqtSignal(int, int)
    exception = pyqtSignal('PyQt_PyObject')

    def __init__(self, team, arch):
        super().__init__()
        self._lp_team = team
        self._launchpad = None
        self._lp_arch = arch
        self._lp_ppa = ""
        self._pkgs = []
        self.debs = []
        self._pool = multiprocessing.dummy.Pool(10)
        self._result = None

    def connect(self):
        try:
            self._launchpad = Launchpad.login_anonymously('kxfed.py', 'production')
            self._lp_team = self._launchpad.people[self._lp_team]
        except HTTPError as e:
            logging.log(0, e.strerror)

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
                subprocess.run(['pkexec', './uninstall_pkg', pkg.binary_name], stdout=subprocess.PIPE)
                # TODO if success!!
                cfg['installed'][pkg.ppa].pop(pkg.id)
                cfg.delete_ppa_if_empty('installed', pkg.ppa)
        cfg['tobeuninstalled'].clear()

    def install_pkgs(self):
        # get list of packages to be installed from cfg, using pop to delete
        for ppa in cfg['tobeinstalled']:
            for pkgid in cfg['tobeinstalled'][ppa]:
                if ppa not in cfg['installing']:
                    cfg['downloading'][ppa] = {}
                pkg = cfg['tobeinstalled'][ppa].pop(pkgid)
                cfg['downloading'][ppa][pkgid] = pkg
                debs_dir = cfg['debs_dir']
                rpms_dir = cfg['rpms_dir']
                self._pool.apply_async(self._get_deb_links_and_download,
                                       (ppa,
                                        pkg,
                                        debs_dir,
                                        rpms_dir,))

        self.progress_adjusted.emit(0, 0)

    def _get_deb_links_and_download(self, ppa, pkg, debs_dir, rpms_dir):
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
            for link in links:
                fp = debs_dir + link['href'].rsplit('/', 1)[-1]
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
                # build_rpms.sh working_dir deb_filepath rpms_dir arch
                result = subprocess.run(['/bin/bash',
                                         '/home/james/Src/kxfed/build_rpms.sh',
                                         debs_dir,
                                         fp,
                                         rpms_dir,
                                         'amd64'],
                                        stdout=subprocess.PIPE).stdout.decode('utf-8')
                logging.log(logging.DEBUG, result)
        except (requests.HTTPError, Exception) as e:
            logging.log(logging.ERROR, traceback.format_exc())
            self.exception.emit(e)

    def _install_rpms(self, pkg):
        subprocess.run(['pkexec', './install_pkg', pkg.rpm_file], stdout=subprocess.PIPE)

