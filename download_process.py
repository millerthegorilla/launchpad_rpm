from package_process import PackageProcess
from kfconf import cfg, debs_dir, pkg_states, add_item_to_section, check_installed
from requests import get, HTTPError
from bs4 import BeautifulSoup
from os.path import isfile, basename
from re import compile
import logging
from threading import RLock
from multiprocessing.dummy import Pool as ThreadPool
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QGuiApplication


class DownloadProcess(PackageProcess):
    total_length = 0
    current_length = 0

    def __init__(self, *args, team_link=None, msg_signal=None, log_signal=None, progress_signal=None):
        super(DownloadProcess, self).__init__(*args, msg_signal=msg_signal, log_signal=log_signal)
        self._section = "downloading"
        self._error_section = "failed_downloading"
        self._path_name = "deb_path"
        self._team_link = team_link
        self._lock = RLock()
        self._thread_pool = ThreadPool(10)
        self._progress_signal = progress_signal
        self._pkgs_complete = 0
        self._pkgs_success = 0
        self._errors = 0

    def prepare_action(self):
        moved = False
        for ppa in pkg_states["tobeinstalled"]:
            for pkg_id in pkg_states["tobeinstalled"][ppa]:
                add_item_to_section(self._section, pkg_states["tobeinstalled"][ppa].pop(pkg_id))
                moved = True
        moved = super().prepare_action() | moved
        cfg.write()
        return moved

    def state_change(self, callback=None):
        self._action_finished_callback = callback
        assert len(self), "state change called without list initialisation.  Call " + \
                          type(self).__qualname__ + \
                          ".read_section()"
        self._pkgs_complete = 0
        self._pkgs_success = 0
        self._errors = 0
        for i in self:
            if not check_installed(i.pkg["name"], i.pkg["version"]):
                self._thread_pool.apply_async(self.__get_deb_link_and_download,
                                              (i.ppa,
                                               i.pkg,
                                               debs_dir,
                                               self._team_link,), callback=self.download_finished)

    @pyqtSlot('PyQt_PyObject')
    def download_finished(self, name):
        self._pkgs_complete += 1
        if success:
            self._pkgs_success += 1
        else:
            self._errors += 1
            self._log_signal.emit("Unable to download " + name + " from launchpad.", logging.ERROR)
        if self._pkgs_complete == len(self):
            cfg.write()
            self._action_finished_callback(1, self._pkgs_success)

    def __get_deb_link_and_download(self, ppa, pkg, debsdir, web_link):
        # threaded function - gets build link from page and then parses that link
        # to obtain the download links for the package, downloads the package
        # and returns a path for the package deb file.
        try:
            html = get(web_link
                       + "/+archive/ubuntu/"
                       + ppa
                       + "/+build/" + pkg["build_link"].rsplit("/", 1)[-1])

            links = BeautifulSoup(html.content, "lxml").find_all("a",
                                                                 href=compile(r""
                                                                              + pkg["name"]
                                                                              + "(.*?)(all|amd64\\.deb)"))
            pkg["deb_link"] = links[[str(basename(x['href'])).split('_')[0] for x in links].index(pkg['name'])]['href']
            fn = basename(pkg["deb_link"])
            fp = debsdir + fn
            if not isfile(fp):
                self._log_signal.emit("Downloading " + pkg["name"] + " from " + pkg['deb_link'], logging.INFO)
                self._msg_signal.emit("Downloading " + pkg["name"])
                with open(fp, "wb+") as f:
                    response = get(pkg["deb_link"], stream=True)
                    tot_length = response.headers.get("content-length")
                    if tot_length is None:  # no content length header
                        f.write(response.content)
                    else:
                        self.total_length += int(tot_length)
                        for data in response.iter_content(chunk_size=1024):
                            f.write(data)
                            self.current_length += len(data)
                            self._progress_signal.emit(self.current_length, self.total_length)
                            QGuiApplication.processEvents()
            pkg["deb_path"] = fp
            return True, pkg["name"]
        except HTTPError as e:
            self._log_signal.emit(e, logging.CRITICAL)
            return False, pkg["name"]


class RPMDownloadProcess(DownloadProcess):
    def __init__(self, *args, team_link=None, msg_signal=None, log_signal=None, progress_signal=None):
        assert (team_link is not None), "In order to create a DownloadProcess, team_link must be defined."
        assert (msg_signal is not None), "In order to create a DownloadProcess, msg_signal must be defined."
        assert (log_signal is not None), "In order to create a DownloadProcess, log_signal must be defined."
        super(RPMDownloadProcess, self).__init__(args,
                                                 team_link=team_link,
                                                 msg_signal=msg_signal,
                                                 log_signal=log_signal,
                                                 progress_signal=progress_signal)
        self._next_section = "converting"

    def state_change(self, callback=None):
        self._action_finished_callback = callback
        super().state_change()


class DEBDownloadProcess(DownloadProcess):
    def __init__(self, *args, team_link=None, msg_signal=None, log_signal=None, progress_signal=None):
        assert (team_link is not None), "In order to create a DownloadProcess, team_link must be defined."
        assert (msg_signal is not None), "In order to create a DownloadProcess, msg_signal must be defined."
        assert (log_signal is not None), "In order to create a DownloadProcess, log_signal must be defined."
        super(DEBDownloadProcess, self).__init__(*args,
                                                 team_link=team_link,
                                                 msg_signal=msg_signal,
                                                 log_signal=log_signal,
                                                 progress_signal=progress_signal)
        self._next_section = "installing"

    def state_change(self, callback=None):
        self._action_finished_callback = callback
        super().state_change()
