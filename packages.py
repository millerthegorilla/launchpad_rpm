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

from txrequests import Session
from launchpadlib.launchpad import Launchpad
from launchpadlib.errors import HTTPError
import logging
import re
from bs4 import BeautifulSoup, SoupStrainer
from twisted.internet import defer
from tvitem import TVItem
import kfconf


class Packages:
    def __init__(self, team, arch):
        self.__lp_team = None
        self.__launchpad = None
        try:
            self.__launchpad = Launchpad.login_anonymously('kxfed.py', 'production')
            self.__lp_team = self.__launchpad.people[team]
        except HTTPError as http_error:
            logging.log(0, str(http_error))
        self.__lp_arch = arch
        self.__lp_ppa = ""
        self.__pkgs = []
        self.debs = []
        self.__strainer = SoupStrainer('a')

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

    @kfconf.cache.cache_on_arguments()
    def populate_pkgs(self, lp_ppa):
        try:
            pkgs = []
            ubuntu = self.__launchpad.distributions["ubuntu"]
            ppa = self.__lp_team.getPPAByName(distribution=ubuntu, name=lp_ppa)

            ds1 = ubuntu.getSeries(name_or_version="trusty")
            ds2 = ubuntu.getSeries(name_or_version="lucid")
            ds3 = ubuntu.getSeries(name_or_version="xenial")
            ds4 = ubuntu.getSeries(name_or_version="bionic")

            d_s = [ds1, ds2, ds3, ds4]
            d_a_s = []
            for i in d_s:
                d_a_s.append(i.getDistroArchSeries(archtag=self.__lp_arch))
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
            # do I need to cache __pkgs in instance variable - why not use a local?
            return pkgs
        except Exception as http_error:
            logging.log(logging.ERROR, str(http_error))

    @defer.inlineCallbacks
    def _get_deb_links_(self, ppa, build_link):
        # https: // twistedmatrix.com / documents / current / api / twisted.internet.defer.html  # inlineCallbacks
        try:
            with Session() as session:
                html = session.get(self.__lp_team.web_link
                                             + '/+archive/ubuntu/'
                                             + ppa
                                             + '/+build/' + build_link)
                content = yield html
                links = BeautifulSoup(content, builder='lxml').find_all('a', href=re.compile(r'all|amd64\.deb'))
                return list(map(lambda x: x['href'], links))
        except Exception as http_error:
            logging.log("error", str(http_error))
