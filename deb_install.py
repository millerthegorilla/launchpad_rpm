from apt.progress.base. import InstallProgress
from apt import DebPackage


class InstProgress(apt.progress.base.InstallProgress):
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


if __name__ == '__main__':
    deb_package = DebPackage()
    deb_package.