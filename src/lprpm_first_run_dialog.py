from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QTimer
from ui.lprpm_first_run_dialog_ui import UiLPRpmFirstRunDialog


class LPRpmFirstRunDialog(QDialog):
    def __init__(self, cache_renew=False):
        super(LPRpmFirstRunDialog, self).__init__()

        # Set up the user interface from Designer.
        self.ui = UiLPRpmFirstRunDialog()
        self.ui.setupUi(self)
        self._timer = QTimer()
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._timer_fire)
        self._timer_id = self._timer.start(500)
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
