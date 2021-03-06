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
from traceback import format_exc
from lprpm_conf import cfg, cache, cache_dir, pkg_states, clean_section, \
                        all_sections_not_installed, ENDED_CANCEL, ENDED_ERR, ENDED_NTD
if cfg['distro_type'] == 'rpm':
    from transaction import RPMTransaction
else:
    from transaction import DEBTransaction


class Packages(QThread):

    _actioning_finished_signal = pyqtSignal()

    def __init__(self, team, arch,
                 msg_signal=None, log_signal=None, progress_signal=None,
                 transaction_progress_signal=None,
                 lock_model_signal=None, list_filling_signal=None,
                 ended_signal=None, request_action_signal=None, populate_pkgs_signal=None,
                 list_filled_signal=None, list_changed_signal=None, action_timer_signal=None,
                 installed_changed_signal=None):
        super().__init__()
        self.team = team
        self._launchpad = None
        self._arch = arch
        self._lp_ppa = None
        self._lp_team = None
        self._lp_team_web_link = None
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
        self._installed_changed_signal = installed_changed_signal
        self._action_timer_signal = action_timer_signal
        self._actioning_finished_signal.connect(self.post_state_change)
        # process handle for the sake of cancelling
        self.process = None
        self._num_processed = 0
        self._transaction = None
        self._teams = None

    def connect(self):
        self._launchpad = Launchpad.login_anonymously('lprpm', 'production', cache_dir, version='devel')
        self._lp_team = self._launchpad.people[self.team]
        self._lp_team_web_link = self._lp_team.web_link

    @property
    def lp_team(self):
        return self._lp_team

    @lp_team.setter
    def lp_team(self, team):
        list = self._launchpad.people.findTeam(text=team)
        self._lp_team = list[0]

    @property
    def team_web_link(self, team):
        return self._team_web_link

    @property
    def ppa(self):
        return self._ppa

    @ppa.setter
    def ppa(self, ppa):
        self._ppa = ppa

    @property
    def arch(self):
        return self._arch

    @property
    def launchpad(self):
        return self._launchpad

    def populate_pkgs(self, ppa, arch):
        self._ppa = ppa
        self._arch = arch
        #  self._list_filling_signal.emit()
        self._thread_pool.apply_async(self._populate_pkg_list, (self._lp_team, ppa, arch,),
                                      callback=self.pkg_populated)

    def pkg_populated(self, pkgs):
        self._list_filled_signal.emit(pkgs)
        self._list_filling_signal.emit(False)
        if self._installed_changed_signal is not None:
            self._installed_changed_signal.emit()

    @cache.cache_on_arguments()
    def _populate_pkg_list(self, team, ppa, arch):
        try:
            pkgs = []
            ubuntu = self._launchpad.distributions["ubuntu"]
            lp_ppa = team.getPPAByName(distribution=ubuntu, name=ppa)

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
                               self.lp_team.display_name,
                               self.lp_team.name,
                               uuid.uuid4().urn]
                        if pkg not in pkgs:
                            pkgs.append(pkg)

            return pkgs
        except HTTPError as http_error:
            self._log_signal.emit(http_error, logging.CRITICAL)

    def post_state_change(self):
        self._progress_signal.emit(0, 0)
        self._transaction_progress_signal.emit(0, 0)
        self._list_changed_signal.emit(self._ppa, self._arch)

    def install_pkgs_button(self):
        clean_section(all_sections_not_installed)
        empty = True
        for section in all_sections_not_installed:
            if bool(pkg_states[section]) is True:
                empty = False
        if empty is True:
            self._ended_signal.emit(ENDED_NTD)
        else:
            try:
                if cfg['distro_type'] == 'rpm':
                    self._transaction = RPMTransaction(team_web_link=self._lp_team_web_link,
                                                       msg_signal=self._msg_signal,
                                                       log_signal=self._log_signal,
                                                       progress_signal=self._progress_signal,
                                                       transaction_progress_signal=self._transaction_progress_signal,
                                                       request_action_signal=self._request_action_signal,
                                                       populate_pkgs_signal=self._populate_pkgs_signal,
                                                       action_timer_signal=self._action_timer_signal,
                                                       list_changed_signal=self._actioning_finished_signal,
                                                       ended_signal=self._ended_signal)
                if cfg['distro_type'] == 'deb':
                    self._transaction = DEBTransaction(team_web_link=self._lp_team_web_link,
                                                       msg_signal=self._msg_signal,
                                                       log_signal=self._log_signal,
                                                       progress_signal=self._progress_signal,
                                                       transaction_progress_signal=self._transaction_progress_signal,
                                                       request_action_signal=self._request_action_signal,
                                                       populate_pkgs_signal=self._populate_pkgs_signal,
                                                       action_timer_signal=self._action_timer_signal,
                                                       list_changed_signal=self._actioning_finished_signal,
                                                       ended_signal=self._ended_signal)
                self._transaction.process()
            except Exception as e:
                self._log_signal.emit(format_exc(), logging.ERROR)
                self._ended_signal.emit(ENDED_ERR)

    def cancel(self):
        if self.process is not None:
            self.process.stdin.write(b"cancel")
            self.process.terminate()
        self._ended_signal.emit(ENDED_CANCEL)
