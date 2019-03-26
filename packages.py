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
from PyQt5.QtCore import pyqtSignal, QObject, QCoreApplication, Qt
from launchpadlib.launchpad import Launchpad
from launchpadlib.errors import HTTPError
from multiprocessing.dummy import Pool as thread_pool
from multiprocessing import Pool as mp_pool
from kfconf import cfg, cache, config_search, pkg_states
import requests
import subprocess
import os
from os.path import basename
from bs4 import BeautifulSoup
import re
import time
import logging
from PyQt5.QtCore import QProcess, pyqtSlot
import uuid

try:
    import rpm
except ImportError as e:
    try:
        import apt
    except ImportError as ee:
        raise Exception(e.args + " : " + ee.args)


class Packages(QObject):

    progress_adjusted = pyqtSignal(int, int)
    transaction_progress_adjusted = pyqtSignal(int, int)
    msg = pyqtSignal(str)
    log = pyqtSignal('PyQt_PyObject', int)
    lock_model = pyqtSignal(bool)

    def __init__(self, team, arch, progress_signal, trans_prog_signal, msg_signal, log_signal, lock_signal):
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
        self.cancel_process = False
        self.installing = False
        self.progress_adjusted.connect(progress_signal)
        self.transaction_progress_adjusted.connect(trans_prog_signal)
        self.msg.connect(msg_signal)
        self.log.connect(log_signal)
        self.lock_model.connect(lock_signal)

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

    def populate_pkgs(self, ppa, arch, callback_function):
        self._thread_pool.apply_async(self.populate_pkg_list, (ppa, arch,),
                                      callback=callback_function)

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
            pass
            self.log.emit(http_error, logging.CRITICAL)

    # def pkg_search(self, sections, pkg_id):
    #     def conf_search(section, key, search_value=None):
    #         if search_value == section[key]:
    #             cfg['found'] = section
    #     for sect in sections:
    #         cfg[sect].walk(conf_search, search_value=pkg_id)
    #         if cfg['found']:
    #             return True
    #     return False
    @staticmethod
    def pkg_search(sections, pkg_id):
        for section in sections:
            for ppa in pkg_states[section]:
                if pkg_id in pkg_states[section][ppa].dict():
                    return True
        return False

    @staticmethod
    def uninstall_pkgs(self):
        # get list of packages to be uninstalled from cfg, using pop to delete
        for ppa in pkg_states['tobeuninstalled']:
            for pkg in pkg_states['tobeuninstalled'][ppa]:
                #subprocess.run(['pkexec', './uninstall_pkg', pkg.binary_name], stdout=subprocess.PIPE)
                # TODO if success!!
                pkg_states['installed'][pkg.ppa].pop(pkg.id)
                cfg.delete_ppa_if_empty('installed', pkg.ppa)
        pkg_states['tobeuninstalled'].clear()

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
        if cfg['convert'] == 'True' and cfg['distro_type'] == 'rpm':
            self.lock_model.emit(True)
            self._thread_pool = thread_pool(10)
            result = self._thread_pool.apply_async(self.convert_packages,
                                                   (deb_paths,))
            if result.get() is True:
                self.lock_model.emit(False)
                QCoreApplication.instance().processEvents()
                if cfg['install'] == 'True':
                    self.lock_model.emit(True)
                    if cfg['distro_type'] == 'rpm':
                        self._thread_pool.apply_async(self._install_rpms, self.finish_install)
                    else:
                        self._install_debs()

    # def continue_convert(self, deb_paths):
    #     # async call convert function allows access to gui to continue
    #     if cfg['convert'] == 'True' and cfg['distro_type'] == 'rpm':
    #         Kxfed.lock_model_signal.emit(True)
    #         self._thread_pool = thread_pool(10)
    #         result = self._thread_pool.apply_async(self.convert_packages,
    #                                                (deb_paths,))
    #         return result
    #
    # def continue_install(self):
    #     if cfg['install'] == 'True':
    #         Kxfed.lock_model_signal.emit(True)
    #         if cfg['distro_type'] == 'rpm':
    #             self._thread_pool.apply_async(self._install_rpms, self.finish_install)
    #         else:
    #             self._install_debs()

    def finish_install(self):
        self.lock_model.emit(False)

    def download_packages(self):
        # get list of packages to be installed from cfg, using pop to delete
        self.log.emit('Downloading Packages', logging.INFO)
        self.progress_adjusted.emit(0, 0)
        deb_links = []
        pkg_states['downloading'] = {}

        for ppa in pkg_states['tobeinstalled']:

            for pkgid in pkg_states['tobeinstalled'][ppa]:
                if ppa not in pkg_states['installing'] and ppa not in pkg_states['installed']:
                    pkg = pkg_states['tobeinstalled'][ppa].pop(pkgid)
                    if ppa not in pkg_states['downloading']:
                        pkg_states['downloading'][ppa] = {}
                    pkg_states['downloading'][ppa][pkgid] = pkg
                    cfg.write()
                    debs_dir = cfg['debs_dir']
                    self.msg.emit("Downloading " + pkg.get('name'))
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
                            self.progress_adjusted.emit(len(data), total_length)
                            total_length = 0
                deb_paths.append(fp)
            pkg['deb_paths'] = deb_paths
            return deb_paths
        except requests.HTTPError as e:
            self.log.emit(e, logging.CRITICAL)

    def convert_packages(self, deb_paths):

        self.log.emit('Converting packages : ' + str(deb_paths), logging.INFO)
        self.progress_adjusted.emit(0, 0)
        deb_pkgs = []
        for deb_list in deb_paths:
            for filepath in deb_list:
                deb_pkgs.append(filepath)

        for deb in deb_pkgs:
            for ppa in pkg_states['downloading']:
                for pkgid in pkg_states['downloading'][ppa]:
                    tag = pkg_states['downloading'][ppa][pkgid]['deb_link'][0]
                    if os.path.basename(deb) == str(tag.contents[0]):
                        pkg = pkg_states['downloading'][ppa].pop(pkgid)
                        if ppa not in pkg_states['converting']:
                            pkg_states['converting'][ppa] = {}
                        pkg_states['converting'][ppa][pkgid] = pkg
        pkg_states['downloading'] = {}

        cfg.write()
        self.log.emit('Converting packages : ' + str(deb_pkgs), logging.INFO)
        self.msg.emit('Converting Packages...')
        try:
            process = subprocess.Popen(['pkexec', '/home/james/Src/kxfed/build_rpms.sh', cfg['rpms_dir'], cfg['arch']] +
                                       deb_pkgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            self.log.emit(e)

        conv = False
        rpm_file_names = []
        while True:
            nextline = process.stdout.readline().decode('utf-8')
            self.log.emit(nextline, logging.INFO)
            if 'Wrote' in nextline:
                rpm_file_names.append(basename(nextline))
            if 'Converted' in nextline:
                rpm_name = nextline[len('Converted '):nextline.index('_')]
                pkg_states['converting'].walk(config_search, search_value=rpm_name)
                if cfg['found']:
                    if not pkg_states['installing']:
                        pkg_states['installing'] = {}
                    if cfg['found'].parent.name not in pkg_states['installing']:
                        pkg_states['installing'][cfg['found'].parent.name] = {}
                    pkg_states['installing'][cfg['found'].parent.name][cfg['found'].name] = \
                        pkg_states['converting'][cfg['found'].parent.name].pop(cfg['found'].name)
                    for fn in rpm_file_names:
                        if rpm_name in fn:
                            pkg_states['installing'][cfg['found'].parent.name][cfg['found'].name]['rpm_path'] = \
                                cfg['rpms_dir'] + fn.rstrip('\r\n')
                    cfg['found'] = {}
                    conv = True
                    self.progress_adjusted.emit(round(100 / len(deb_pkgs)), 100)
                    self.msg.emit(nextline)
                else:
                    conv = False
            if nextline == '' and process.poll() is not None:
                break
        # TODO ********* delete deb file if package is successfully converted
        # TODO ********* if preferences say so
        if conv is True:
            cfg.filename = (cfg['config']['dir'] + cfg['config']['filename'])
            cfg.write()
            for ppa in pkg_states['converting']:
                if pkg_states['converting'][ppa]:
                    for pkg in pkg_states['converting'][ppa]:
                        self.log('Error - did not convert ' + str(pkg.name), logging.INFO)
            pkg_states['converting'] = {}
            return True
        else:
            self.log(Exception("There is an error with the bash script when converting."), logging.CRITICAL)

    def _install_rpms(self):
        self.msg.emit("Installing packages...")
        rpm_links = []
        for ppa in pkg_states['installing']:
            for pkg in pkg_states['installing'][ppa]:
                rpm_links.append(basename(pkg_states['installing'][ppa][pkg]['rpm_path']))
        rpm_links.append('uninstalling')
        for ppa in pkg_states['uninstalling']:
            for pkg in pkg_states['uninstalling'][ppa]:
                rpm_links.append(pkg_states['uninstalling'][ppa][pkg]['name'])
        try:
            process2 = subprocess.Popen(['/home/james/Src/kxfed/inst_rpms.py', cfg['rpms_dir']] + rpm_links, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            self.log.emit(e, logging.CRITICAL)

        while True:
            line = process2.stdout.readline().decode('utf-8')
            self.log.emit(line, logging.INFO)
            if line:
                if 'kxfedlog' in line:
                    self.log.emit(line.lstrip('kxfedlog '), logging.INFO)
                elif 'kxfedexcept' in line:
                    self.log.emit(line.lstrip('kxfedexcept '), logging.CRITICAL)
                elif 'kxfedmsg' in line:
                    self.msg.emit(line.lstrip('kxfedmsg '))
                elif 'kxfedprogress' in line:
                    sig = line.split(' ')
                    self.progress_adjusted.emit(sig[1], sig[2])
                elif 'kxfedtransprogress' in line:
                    sig = line.split(' ')
                    self.transaction_progress_adjusted(sig[1], sig[2])
                elif 'kxfedinstalled' in line:
                    self.msg.emit('Installed ' + line.lstrip('kxfedinstalled'))
                    # TODO move pkg in config from installing to installed
                    # TODO set checkstate of package to installed
                elif 'kxfeduninstalled' in line:
                    self.msg.emit('Uninstalled ' + line.lstrip('kxfeduninstalled'))
                    # TODO delete package from uninstalled state
                    # TODO change highlighted color of checkbox row to normal color
                    # TODO delete rpm if it says so in the preferences
                elif 'kxfedstop' in line:
                    break
                else:
                    self.log.emit(line, logging.INFO)
            # if line == '' and process.poll() is not None:
            #     break

    @pyqtSlot(int, QProcess.ExitStatus)
    def catch_signal_install(self, exitcode, exitstatus):
        self.installing = False
        if exitcode != 0 | exitstatus != QProcess.NormalExit:
            self.log.emit("error processing install_rpms", logging.ERROR)

    def _install_debs(self):
        pass
