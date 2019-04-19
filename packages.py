#    This file is part of rpm_maker.

#    rpm_maker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    rpm_maker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

import logging
import time
import uuid
from multiprocessing.dummy import Pool as ThreadPool

from PyQt5.QtCore import pyqtSignal, QThread
from launchpadlib.errors import HTTPError
from launchpadlib.launchpad import Launchpad

from kfconf import cfg, cache, clean_section
from download_process import DownloadProcess
from conversion_process import ConversionProcess
from action_process import ActionProcess
try:
    import rpm
except ImportError as e:
    try:
        import apt
    except ImportError as ee:
        raise Exception(str(e.args) + " : " + str(ee.args))


# TODO log messages are being written twice.
# TODO why is it stopping?


class Packages(QThread):
    download_finished_signal = pyqtSignal('PyQt_PyObject')
    conversion_finished_signal = pyqtSignal(bool)
    actioning_finished_signal = pyqtSignal()

    def __init__(self, team, arch,
                 msg_signal, log_signal, progress_signal,
                 transaction_progress_signal,
                 lock_model_signal, list_filling_signal,
                 cancel_signal, request_action_signal,
                 list_filled_signal):
        super().__init__()
        self.team = team
        self._launchpad = None
        self.arch = arch
        self._lp_ppa = None
        self._lp_team = None
        self._ppa = ''
        self._thread_pool = ThreadPool(10)
        self.cancel_process = False

        # signals from above
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self._progress_signal = progress_signal
        self._transaction_progress_signal = transaction_progress_signal
        self._lock_model_signal = lock_model_signal
        self._list_filling_signal = list_filling_signal
        self._cancel_signal = cancel_signal
        self._request_action_signal = request_action_signal
        self._list_filled_signal = list_filled_signal

        # process handle for the sake of cancelling
        self.process = None

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

    def populate_pkgs(self, ppa, arch):
        self._list_filling_signal.emit()
        self._thread_pool.apply_async(self._populate_pkg_list, (ppa, arch,),
                                      callback=self._list_filled_signal.emit)

    @cache.cache_on_arguments()
    def _populate_pkg_list(self, ppa, arch):
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
            self._log_signal.emit(http_error, logging.CRITICAL)

    def install_pkgs_button(self):
        try:
            ts = rpm.TransactionSet()
            if ts.dbMatch('name', 'python3-rpm').count() == 1:
                cfg['distro_type'] = 'rpm'
        except Exception as e:
            cfg['distro_type'] = 'deb'
        clean_section(['tobeinstalled', 'downloading', 'converting', 'installing'])
        pkg_processes = [DownloadProcess(team_link=self.lp_team.web_link,
                                         msg_signal=self._msg_signal,
                                         log_signal=self._log_signal,
                                         progress_signal=self._progress_signal) if cfg['download'] else None,
                         ConversionProcess(msg_signal=self._msg_signal,
                                           log_signal=self._log_signal,
                                           progress_signal=self._progress_signal) if cfg['convert'] else None,
                         ActionProcess(msg_signal=self._msg_signal,
                                       log_signal=self._log_signal,
                                       progress_signal=self._progress_signal,
                                       transaction_progress_signal=self._transaction_progress_signal,
                                       request_action_signal=self._request_action_signal)
                         if cfg.as_bool('install') or cfg.as_bool('uninstall') else None]
        for pkg_process in pkg_processes:
            pkg_process.prepare_action()
            if pkg_process.read_section():
                success, number = pkg_process.state_change()
                if pkg_process.section is not 'actioning':
                    if not success:
                        self._msg_signal("Not all packages from " + pkg_process.section + " were successful")
                        self._log_signal("Not all packages from " + pkg_process.section + " were successful",
                                         logging.INFO)
                pkg_process.move_cache()

    def cancel(self):
        self.cancel_process = True
        if self.process is not None:
            self.process.stdin.write(b"cancel")
            self.process.terminate()
        self.cancel_signal.emit()
