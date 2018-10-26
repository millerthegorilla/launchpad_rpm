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

from urllib import error, request
from launchpadlib.launchpad import Launchpad
import logging, re
from bs4 import BeautifulSoup


class Packages():
    def __init__(self, team, ppa, arch):
        self.launchpad = Launchpad.login_anonymously('kxfed.py', 'production')
        self.lp_team = team
        self.lp_ppa = ppa
        self.lp_arch = arch
        self.debs = []

    def get(self, callback):
        self._get()
        self._get_deb_links()
        callback()

    def _get(self):
        try:
            team = self.launchpad.people[self.lp_team]
            ubuntu = self.launchpad.distributions["ubuntu"]

            ppa = team.getPPAByName(distribution=ubuntu, name=self.lp_ppa)

            ds1 = ubuntu.getSeries(name_or_version="trusty")
            ds2 = ubuntu.getSeries(name_or_version="lucid")
            ds3 = ubuntu.getSeries(name_or_version="xenial")
            ds4 = ubuntu.getSeries(name_or_version="bionic")

            d_s = [ds1,ds2,ds3,ds4]
            d_a_s = []
            for i in d_s:
                d_a_s.append(i.getDistroArchSeries(archtag=self.lp_arch))
            p_b_h = []
            for i in d_a_s:
                p_b_h.append(ppa.getPublishedBinaries(order_by_date=True, pocket="Release", status="Published", distro_arch_series=i))

            self.build_links = list()

            for b in p_b_h:
                if len(b):
                    for i in b:
                        if i.build_link[8:] not in self.build_links:
                            self.build_links.append([i.build_link[8:],
                                                  i.binary_package_name,
                                                  i.binary_package_version,
                                                  i.resource_type_link])

        except error.HTTPError as http_error:
            logging.log(http_error.content)

    def _get_deb_links(self):
        url_prefix = 'https://launchpad.net/~kxstudio-debian/+archive/ubuntu/plugins/+build/'
        for build in self.build_links:
            regex = r"(\d+$)"
            buildnum = re.search(regex, build[0], re.MULTILINE)
            url = url_prefix + buildnum[0]
            html = request.urlopen(url).read()
            soup = BeautifulSoup(html)

            links = soup.find_all('a')
            self.debs.append(build + list(filter(lambda x: 'deb' in x and self._arch in x or 'all' in x, links)))
