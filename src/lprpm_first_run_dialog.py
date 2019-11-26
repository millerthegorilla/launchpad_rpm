from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QTimer
from ui.lprpm_first_run_dialog_ui import UiLPRpmFirstRunDialog
import pickle
import logging


class LPRpmFirstRunDialog(QDialog):
    def __init__(self, log_signal, message_user_signal, cache_renew=False):
        super(LPRpmFirstRunDialog, self).__init__()
        self.log_signal = log_signal
        self.message_user_signal = message_user_signal
        # Set up the user interface from Designer.
        self.ui = UiLPRpmFirstRunDialog()
        self.ui.setupUi(self)
        self._timer = QTimer()
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._timer_fire)
        self._timer_id = self._timer.startTimer(500)
        if cache_renew is False:
            self.ui.label.setText("First run... initialising team names from launchpad.net."
                                  "  The result is cached, so you won't have to wait again,"
                                  " unless you renew the cache.")
        else:
            self.ui.label.setText("Renewing Caches, updating team names from launchpad.net")
        self.show()

    def _timer_fire(self):
        timer_num = self.ui.progressBar.value() + 1
        self.ui.progressBar.setValue(timer_num % 100)

    def killTimer(self):
        super().killTimer(self._timer_id)

    def _team_data_wrapper(self):
        if cfg["renew_names"] is True:
            self._thread_pool.apply_async(self._team_data, (cfg['cache']['initiated'],), callback=self._team_data_obtained)

    def _team_data_obtained(self, team_list):
        self.message_user_signal.emit("Finished updating list of teams from launchpad. Result is cached. "
                                      "See preferences to renew")
        self.log_signal.emit("Finished initialising team list, The result is cached and you can renew"
                             "caches if you wish to reinstall this list", level=logging.INFO)
        with open('teamnames.pkl', 'wb') as f:
            pickle.dump(team_list, f)
        self._team_data_list = team_list

    #@cache.cache_on_arguments()
    def _team_data(self, initiation_time):
        #self.message_user("Updating list of teams from launchpad.")
        self.log_signal.emit("Initialising team list. The result is cached and you can renew"
                                   "caches if you wish to reinitialise this list", level=logging.INFO)
        return [x.name for x in self.lprpm.pkg_model.packages.launchpad.people.findTeam(text="")]

