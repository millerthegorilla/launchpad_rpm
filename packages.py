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
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
from launchpadlib.errors import HTTPError
from launchpadlib.launchpad import Launchpad

from kfconf import cfg, cache, pkg_states, clean_section, has_pending, \
                   ENDED_SUCC, ENDED_CANCEL, ENDED_ERR
from download_process import DownloadProcess
from conversion_process import ConversionProcess
from action_process import ActionProcess
from traceback import format_exc

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
    actioning_finished_signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, team, arch,
                 msg_signal=None, log_signal=None, progress_signal=None,
                 transaction_progress_signal=None,
                 lock_model_signal=None, list_filling_signal=None,
                 ended_signal=None, request_action_signal=None, populate_pkgs_signal=None,
                 list_filled_signal=None, list_changed_signal=None, action_timer_signal=None):
        super().__init__()
        self.team = team
        self._launchpad = None
        self._arch = arch
        self._lp_ppa = None
        self._lp_team = None
        self._ppa = ''
        self._thread_pool = ThreadPool(10)
        self._cancel_process = False
        self._success = True
        # signals from above
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self._progress_signal = progress_signal
        self._transaction_progress_signal = transaction_progress_signal
        self._lock_model_signal = lock_model_signal
        self._list_filling_signal = list_filling_signal
        self._ended_signal = ended_signal
        self._request_action_signal = request_action_signal
        self._populate_pkgs_signal = populate_pkgs_signal
        self._list_filled_signal = list_filled_signal
        self._list_changed_signal = list_changed_signal
        self.actioning_finished_signal.connect(self.state_changed)
        self._action_timer_signal = action_timer_signal
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

    @property
    def arch(self):
        return self._arch

    def populate_pkgs(self, ppa, arch):
        self._ppa = ppa
        self._arch = arch
        #  self._list_filling_signal.emit()
        self._thread_pool.apply_async(self._populate_pkg_list, (ppa, arch,),
                                      callback=self.pkg_populated)

    def pkg_populated(self, pkgs):
        self._list_filled_signal.emit(pkgs)
        self._list_filling_signal.emit(False)

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
        pkg_processes = self._mk_pkg_process()
        i = 0
        try:
            while i < len(pkg_processes):
                pkg_process = pkg_processes[i]
                if pkg_process.prepare_action() is True:
                    pkg_processes = self._mk_pkg_process()
                    i = 0
                    continue
                pkg_process.read_section()
                if type(pkg_process) is ActionProcess:
                    self.actioning_finished_signal.connect(self.state_changed)

                if len(pkg_process):
                    # self._thread_pool.terminate()
                    # self._thread_pool = ThreadPool(10)
                    self._thread_pool.apply_async(pkg_process.state_change,
                                                  (self.actioning_finished_signal,))
                i += 1
        except Exception as e:
            self._log_signal.emit(format_exc(), logging.ERROR)
            self._ended_signal.emit(ENDED_ERR)

    @pyqtSlot('PyQt_PyObject')
    def state_changed(self, result):
        number, success, pkg_process = result
        try:
            if not success:
                self._msg_signal.emit("Not all packages from " + pkg_process.section + " were successful")
                self._log_signal.emit("Not all packages from " + pkg_process.section + " were successful",
                                    logging.INFO)
            pkg_process.move_cache()
            # self._populate_pkgs_signal.emit()
            if success and not type(pkg_process) is ActionProcess:
                self.install_pkgs_button()
            self._list_changed_signal.emit(self.ppa, self.arch)
            if success:
                self._ended_signal.emit(ENDED_SUCC)
                self._action_timer_signal.emit(False)
            else:
                self._ended_signal.emit(ENDED_ERR)
        except FileNotFoundError as e:
            exc = str(e).split(" ")
            pkg_states['uninstalling'][exc[2]].pop(exc[3])
            self._list_changed_signal.emit()
            self._log_signal.emit(format_exc(), logging.ERROR)
            self._ended_signal.emit(ENDED_ERR)
        except Exception as e:
            self._log_signal.emit(format_exc(), logging.ERROR)
            self._ended_signal.emit(ENDED_ERR)

    def _mk_pkg_process(self):
        pkg_processes = []
        try:
            if has_pending('downloading') or has_pending('tobeinstalled') and cfg.as_bool('download'):
                pkg_processes.append(DownloadProcess(team_link=self.lp_team.web_link,
                                                     msg_signal=self._msg_signal,
                                                     log_signal=self._log_signal,
                                                     progress_signal=self._progress_signal))
            if has_pending('converting') and cfg.as_bool('convert'):
                pkg_processes.append(ConversionProcess(msg_signal=self._msg_signal,
                                                       log_signal=self._log_signal,
                                                       progress_signal=self._progress_signal,
                                                       transaction_progress_signal=self._transaction_progress_signal))
            if has_pending('installing') or has_pending('uninstalling'):
                pkg_processes.append(ActionProcess(msg_signal=self._msg_signal,
                                                   log_signal=self._log_signal,
                                                   progress_signal=self._progress_signal,
                                                   transaction_progress_signal=self._transaction_progress_signal,
                                                   request_action_signal=self._request_action_signal,
                                                   populate_pkgs_signal=self._populate_pkgs_signal,
                                                   action_timer_signal=self._action_timer_signal))
            return pkg_processes
        except Exception as e:
            raise

    def cancel(self):
        if self.process is not None:
            self.process.stdin.write(b"cancel")
            self.process.terminate()
        self._ended_signal.emit(ENDED_CANCEL)
