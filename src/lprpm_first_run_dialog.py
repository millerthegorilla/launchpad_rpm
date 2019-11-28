from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QTimer
from ui.lprpm_first_run_dialog_ui import UiLPRpmFirstRunDialog


class LPRpmFirstRunDialog(QDialog):
    def __init__(self, mainw, team_signal, log_signal, message_user_signal, cache_renew=False):
        super(LPRpmFirstRunDialog, self).__init__(mainw)
        self.team_signal = team_signal
        self.log_signal = log_signal
        self.message_user_signal = message_user_signal
        # Set up the user interface from Designer.
        self.ui = UiLPRpmFirstRunDialog()
        self.ui.setupUi(self)
        self.ui.progressBar.setValue(0)
        self._timer = QTimer(self)
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._timer_fire)
        self._timer.start(2000)
        if cache_renew is False:
            self.ui.label.setText("First run... initialising team names from launchpad.net."
                                  "  The result is cached, so you won't have to wait again,"
                                  " unless you renew the cache.  Can take over 3 minutes.")
        else:
            self.ui.label.setText("Renewing Caches, updating team names from launchpad.net.  "
                                  "Can take over three minutes")
        self.team_signal.emit()

    def _timer_fire(self):
        timer_num = self.ui.progressBar.value() + 1
        self.ui.progressBar.setValue(timer_num % 100)

    # def killTimer(self):
    #     super().killTimer(self._timer_id)

