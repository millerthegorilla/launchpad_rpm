from abc import abstractmethod
import logging
from kfconf import cfg, has_pending, clean_section, ENDED_ERR, ENDED_SUCC
from action_process import ActionProcess
from conversion_process import ConversionProcess
from traceback import format_exc
if cfg['distro_type'] == 'rpm':
    from download_process import RPMDownloadProcess
else:
    from download_process import DEBDownloadProcess


class Transaction(list):

    def __init__(self, team_web_link=None,
                 msg_signal=None,
                 log_signal=None,
                 progress_signal=None,
                 transaction_progress_signal=None,
                 request_action_signal=None,
                 populate_pkgs_signal=None,
                 action_timer_signal=None,
                 list_changed_signal=None,
                 ended_signal=None):
        super(Transaction, self).__init__()
        self._team_web_link = team_web_link
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self._progress_signal = progress_signal
        self._transaction_progress_signal = transaction_progress_signal
        self._request_action_signal = request_action_signal
        self._populate_pkgs_signal = populate_pkgs_signal
        self._action_timer_signal = action_timer_signal
        self._list_changed_signal = list_changed_signal
        self._ended_signal = ended_signal
        self._num = 0

    @abstractmethod
    def _mk_pkg_process(self):
        pass

    def process(self):
        self._num = 0
        self._process()

    # def __iter__(self):
    #     yield self._process

    def __next__(self):
        self._num += 1
        self._process(self._num)

    def _process(self, num=None):
        num = num if num is not None else 0
        if num >= len(self):
            raise StopIteration()
        if self[num].prepare_action():
            self.clear()
            self._mk_pkg_process()
            self._num = 0
        else:
            self[num].read_section()
            self[num].state_change(callback=self._state_changed)

    def _state_changed(self, num_of_errors, num_of_success):
        try:
            if num_of_errors:
                self._msg_signal.emit("Not all packages from " + self[self._num].section + " were successful. " +
                                      str(num_of_errors) + " packages out of " + str(num_of_errors + num_of_success) +
                                      "were not processed.")
                self._log_signal.emit("Not all packages from " + self[self._num].section + " were successful. " +
                                      str(num_of_errors) + " packages out of " + str(num_of_errors + num_of_success) +
                                      "were not processed.",
                                      logging.INFO)
            self[self._num].move_cache()
            self._list_changed_signal.emit()
            if not num_of_errors and type(self[self._num]) is ActionProcess:
                self._ended_signal.emit(ENDED_SUCC)
                self._action_timer_signal.emit(False)
            elif num_of_errors and type(self[self._num]) is ActionProcess:
                self._ended_signal.emit(ENDED_ERR)
            else:
                self._num += 1
                next(self)
        except FileNotFoundError as e:
            # exc = str(e).split(" ")
            self._log_signal.emit(format_exc(), logging.ERROR)
            self._ended_signal.emit(ENDED_ERR)
        except Exception as e:
            self._log_signal.emit(format_exc(), logging.ERROR)
            self._ended_signal.emit(ENDED_ERR)


class RPMTransaction(Transaction):
    def __init__(self, team_web_link=None,
                 msg_signal=None,
                 log_signal=None,
                 progress_signal=None,
                 transaction_progress_signal=None,
                 request_action_signal=None,
                 populate_pkgs_signal=None,
                 action_timer_signal=None,
                 list_changed_signal=None,
                 ended_signal=None):
        super(RPMTransaction, self).__init__(team_web_link=team_web_link,
                                             msg_signal=msg_signal,
                                             log_signal=log_signal,
                                             progress_signal=progress_signal,
                                             transaction_progress_signal=transaction_progress_signal,
                                             request_action_signal=request_action_signal,
                                             populate_pkgs_signal=populate_pkgs_signal,
                                             action_timer_signal=action_timer_signal,
                                             list_changed_signal=list_changed_signal,
                                             ended_signal=ended_signal)

        self._mk_pkg_process()
        self.process()

    def _mk_pkg_process(self):
        clean_section(['tobeinstalled', 'downloading', 'converting', 'installing'])
        try:
            if has_pending('downloading') or has_pending('tobeinstalled') and cfg.as_bool('download'):
                self.append(RPMDownloadProcess(team_link=self._team_web_link,
                                               msg_signal=self._msg_signal,
                                               log_signal=self._log_signal,
                                               progress_signal=self._progress_signal))
            if has_pending('converting') or len(self) == 1 and cfg.as_bool('convert'):
                self.append(ConversionProcess(msg_signal=self._msg_signal,
                                              log_signal=self._log_signal,
                                              progress_signal=self._progress_signal,
                                              transaction_progress_signal=self._transaction_progress_signal))
            if (has_pending('installing') or
                has_pending('uninstalling') or
                len(self) >= 1) and (cfg.as_bool('install') or
                                              cfg.as_bool('uninstall')):
                self.append(ActionProcess(msg_signal=self._msg_signal,
                                          log_signal=self._log_signal,
                                          progress_signal=self._progress_signal,
                                          transaction_progress_signal=self._transaction_progress_signal,
                                          request_action_signal=self._request_action_signal,
                                          populate_pkgs_signal=self._populate_pkgs_signal,
                                          action_timer_signal=self._action_timer_signal))
        except Exception as e:
            self._log_signal.emit(str(e), logging.CRITICAL)


class DEBTransaction(Transaction):
    def __init__(self, team_web_link=None,
                 msg_signal=None,
                 log_signal=None,
                 progress_signal=None,
                 transaction_progress_signal=None,
                 request_action_signal=None,
                 populate_pkgs_signal=None,
                 action_timer_signal=None,
                 list_changed_signal=None,
                 ended_signal=None):
        super(DEBTransaction, self).__init__(team_web_link=team_web_link,
                                             msg_signal=msg_signal,
                                             log_signal=log_signal,
                                             progress_signal=progress_signal,
                                             transaction_progress_signal=transaction_progress_signal,
                                             request_action_signal=request_action_signal,
                                             populate_pkgs_signal=populate_pkgs_signal,
                                             action_timer_signal=action_timer_signal,
                                             list_changed_signal=list_changed_signal,
                                             ended_signal=ended_signal)
        self._mk_pkg_process()
        self.process()

    def _mk_pkg_process(self):
        clean_section(['tobeinstalled', 'downloading', 'converting', 'installing'])
        try:
            if has_pending('downloading') or has_pending('tobeinstalled') and cfg.as_bool('download'):
                self.append(DEBDownloadProcess(team_link=self._team_web_link,
                                               msg_signal=self._msg_signal,
                                               log_signal=self._log_signal,
                                               progress_signal=self._progress_signal))
            if (has_pending('installing') or
                has_pending('uninstalling') or
                len(self) == 1) and (cfg.as_bool('install') or
                                              cfg.as_bool('uninstall')):
                self.append(ActionProcess(msg_signal=self._msg_signal,
                                          log_signal=self._log_signal,
                                          progress_signal=self._progress_signal,
                                          transaction_progress_signal=self._transaction_progress_signal,
                                          request_action_signal=self._request_action_signal,
                                          populate_pkgs_signal=self._populate_pkgs_signal,
                                          action_timer_signal=self._action_timer_signal))
        except Exception as e:
            self._log_signal.emit(str(e), logging.CRITICAL)
