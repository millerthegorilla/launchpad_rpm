from package_process import PackageProcess
from kfconf import debs_dir, cfg, pkg_states, add_item_to_section, delete_ppa_if_empty
from requests import get, HTTPError
from bs4 import BeautifulSoup
from os.path import isfile
from re import compile
import logging
from threading import RLock
from multiprocessing.dummy import Pool as ThreadPool


class DownloadProcess(PackageProcess, list):
    def __init__(self, *args, team_link=None, msg_signal=None, log_signal=None, progress_signal=None):
        assert(team_link is not None), "In order to create a DownloadProcess, team_link must be defined."
        super(DownloadProcess, self).__init__(args)
        self._section = "downloading"
        self._error_section = "failed_download"
        self._team_link = team_link
        self._lock = RLock()
        self._thread_pool = ThreadPool(10)
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self._progress_signal = progress_signal
        self._total_length = 0
        self._current_length = 0

    def read_section(self):
        """overridding method from super class, to move packages from tobeinstalled to downloading
            I think this might be better in packages.py, with a confirmation dialog listing the packages
            to be downloaded, before transferring them to the download section using this code."""
        for ppa in pkg_states['tobeinstalled']:
            for pkg_id in pkg_states['tobeinstalled'][ppa]:
                add_item_to_section(self._section, pkg_states['tobeinstalled'][ppa].pop(pkg_id))
        super().read_section()

    def state_change(self):
        assert len(self), "state change called without list initialisation.  Call " + \
                          type(self).__qualname__ + \
                          ".read_section()"
        pkgs_complete = 0
        pkgs_success = 0
        for i in self:
            if not self.check_installed(i.pkg['name']):
                result = self._thread_pool.apply_async(self.__get_deb_link_and_download,
                                                       (i.ppa,
                                                        i.pkg,
                                                        debs_dir,
                                                        self._team_link,))
                success, name = result.get()
                pkgs_complete += 1
                if success:
                    pkgs_success += 1
                else:
                    if i.pkg['name'] == name:
                        self._log_signal.emit("Unable to download " + name + " from launchpad.", logging.ERROR)
        while 1:
            if pkgs_complete == len(self):
                cfg.write()
                return 0, pkgs_success
            else:
                return -1, pkgs_success

    def __get_deb_link_and_download(self, ppa, pkg, debsdir, web_link):
        # threaded function - gets build link from page and then parses that link
        # to obtain the download links for the package, downloads the package
        # and returns a path for the package deb file.
        try:
            html = get(web_link
                       + '/+archive/ubuntu/'
                       + ppa
                       + '/+build/' + pkg['build_link'].rsplit('/', 1)[-1])

            links = BeautifulSoup(html.content, 'lxml').find_all('a',
                                                                 href=compile(r''
                                                                              + pkg['name']
                                                                              + '(.*?)(all|amd64\\.deb)'))
            assert len(links) == 1
            pkg['deb_link'] = links[0]
            link = links[0]
            # deb_paths = []
            # for link in links:
            fn = link['href'].rsplit('/', 1)[-1]
            fp = debsdir + fn
            if not isfile(fp):
                self._log_signal.emit("Downloading " + pkg['name'] + ' from ' + str(link['href']), logging.INFO)
                self._msg_signal.emit("Downloading " + pkg['name'])
                with open(fp, "wb+") as f:
                    response = get(link['href'], stream=True)
                    total_length = response.headers.get('content-length')
                    if total_length is None:  # no content length header
                        f.write(response.content)
                    else:
                        self._total_length += int(total_length)

                        for data in response.iter_content(chunk_size=1024):
                            f.write(data)
                            self._lock.acquire()
                            self._current_length += len(data)
                            self._progress_signal.emit(self._current_length, self._total_length)
                            self._lock.release()
            pkg['deb_path'] = fp
            return pkg['name'], True
        except HTTPError as e:
            self._log_signal.emit(e, logging.CRITICAL)

