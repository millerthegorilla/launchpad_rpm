from apt.progress.base import InstallProgress, OpProgress
from apt.debfile import DebPackage
from apt.cache import Cache
import sys


class InstProgress(InstallProgress):
    def __init__(self):
        super().__init__()

    def start_update(self):
        # type: () -> None
        """(Abstract) Start update."""

    def finish_update(self):
        # type: () -> None
        """(Abstract) Called when update has finished."""

    def error(self, pkg, errormsg):
        # type: (str, str) -> None
        """(Abstract) Called when a error is detected during the install."""

    def conffile(self, current, new):
        # type: (str, str) -> None
        """(Abstract) Called when a conffile question from dpkg is detected."""

    def status_change(self, pkg, percent, status):
        # type: (str, float, str) -> None
        """(Abstract) Called when the APT status changed."""


class OProgress(OpProgress):
    def __init__(self):
        super().__init__()

    def done(self):
        super().done(self)

    def update(self, percent=None):
        super().update(percent)


if __name__ == '__main__':
    oprogress = OProgress()
    cache = Cache(progress=oprogress)
    for filename in sys.argv[2:]:
        if "uninstalling" in filename:
            pass
