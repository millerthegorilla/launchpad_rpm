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

import requests
from launchpadlib.launchpad import Launchpad
import logging, re
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool
from config_init import KFConf


class Packages:
    def __init__(self, team, arch):

        self.__lp_team = None
        self.__launchpad = None
        try:
            self.__launchpad = Launchpad.login_anonymously('kxfed.py', 'production')
            self.__lp_team = self.__launchpad.people[team]
        except requests.HTTPError as http_error:
            logging.log(0, str(http_error))
        self.__lp_arch = arch
        self.__lp_ppa = ""
        self.__pkgs = []
        self.debs = []
        # self._pool = ThreadPool(10)  # change th

    @property
    def lp_team(self):
        return self.__lp_team

    @property
    def ppa(self):
        pass

    @ppa.setter
    def ppa(self, ppa):
        self.__lp_ppa = ppa


    @property
    def pkgs(self):
        return self.__pkgs

    def get(self, callback):
        # TODO multithreading
        self._get_()
        self._get_deb_links_()
        callback()

    @KFConf.cache.cache_on_arguments()
    def populate_pkgs(self, lp_ppa):
        try:
            self.__pkgs = []
            ubuntu = self.__launchpad.distributions["ubuntu"]
            ppa = self.__lp_team.getPPAByName(distribution=ubuntu, name=lp_ppa)

            ds1 = ubuntu.getSeries(name_or_version="trusty")
            ds2 = ubuntu.getSeries(name_or_version="lucid")
            ds3 = ubuntu.getSeries(name_or_version="xenial")
            ds4 = ubuntu.getSeries(name_or_version="bionic")

            d_s = [ds1,ds2,ds3,ds4]
            d_a_s = []
            for i in d_s:
                d_a_s.append(i.getDistroArchSeries(archtag=self.__lp_arch))
            p_b_h = []
            for i in d_a_s:
                p_b_h.append(ppa.getPublishedBinaries(order_by_date=True, pocket="Release", status="Published", distro_arch_series=i))

            for b in p_b_h:
                if len(b):
                    for i in b:
                        if i.build_link[8:] not in self.__pkgs:
                            self.__pkgs.append([i.build_link[8:],
                                                i.binary_package_name,
                                                i.binary_package_version,
                                                i.resource_type_link])
            return self.__pkgs

        except requests.HTTPError as http_error:
            logging.log("error", str(http_error))

    def _get_deb_links_(self):
        # TODO change below
        url_prefix = 'https://launchpad.net/~kxstudio-debian/+archive/ubuntu/plugins/+build/'
        urls = []
        for build in self.build_links:
            regex = r"(\d+$)"
            buildnum = re.search(regex, build[0], re.MULTILINE)
            urls.append([build, url_prefix + buildnum[0]])
        #multithread
        self._pool = ThreadPool(10)
        self.debs.append(self._pool.map(self.worker, urls))
        self._pool.close()
        self._pool.join()

    def worker(self, build_url):
        try:
            html = requests.get(build_url[1]).content
            soup = BeautifulSoup(html)
            links = soup.find_all('a')
            build_url[0] + list(filter(lambda x: 'deb' in x and self.__lp_arch in x or 'all' in x, links))
        except requests.HTTPError as httperror:
            logging.log("error", str(httperror))