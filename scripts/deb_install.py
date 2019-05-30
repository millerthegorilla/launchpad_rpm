from apt.progress.base import InstallProgress, OpProgress
from apt.debfile import DebPackage
from apt.cache import Cache, FetchFailedException
import apt_pkg
import sys
from multiprocessing.dummy import Pool as thread_pool


class InstProgress(InstallProgress):
    def __init__(self, type):
        self.type = type
        super().__init__()

    def start_update(self):
        # type: () -> None
        """(Abstract) Start update."""
        print("kxfedmsg started " + self.type)
        print("kxfedlog started " + self.type)

    def finish_update(self):
        # type: () -> None
        """(Abstract) Called when update has finished."""
        print("kxfedmsg finished " + self.type)
        print("kxfedlog finished " + self.type)

    def error(self, pkg, errormsg):
        # type: (str, str) -> None
        """(Abstract) Called when a error is detected during the install."""
        print("kxfedexcept Error in " + pkg + " Error is " + errormsg)

    def conffile(self, current, new):
        # type: (str, str) -> None
        """(Abstract) Called when a conffile question from dpkg is detected."""
        pass

    # def status_change(self, pkg, percent, status):
    #     # type: (str, float, str) -> None
    #     """(Abstract) Called when the APT status changed."""
    #     print('kxfedprogress ' + str(percent) + " 100")


class OProgress(OpProgress):
    def __init__(self):
        super().__init__()

    def done(self):
        super().done()

    def update(self, percent=None):
        super().update(percent)


def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError


class DebInstall:
    def __init__(self):
        self.debs_dir = sys.argv[1]
        self.purge_conf = str_to_bool(sys.argv[2])
        self.auto_fix_install = str_to_bool(sys.argv[3])
        self.auto_fix_delete = str_to_bool(sys.argv[4])
        self.deleting = False
        self.install_list = []
        self.instprogress = InstProgress("installing")
        self.delprogress = InstProgress("deleting")
        self.oprogress = OProgress()
        self.cache = Cache(progress=self.oprogress)
        self.stop = False

    def prepare(self):
        try:
            self.cache.update()
        except FetchFailedException as e:
            print('kxfedexcept Unable to refresh Cache, check connection')
            print('kxfedmsg Unable to refresh Cache, check connection')
            sys.stdout.flush()
            sys.exit(1)
        for filename in sys.argv[6:]:
            if "uninstalling" in filename:
                pkg = self.cache[filename.replace('uninstalling', '')]
                # this should leave pkg of type Package
                if pkg.is_installed():
                    pkg.mark_delete(self.auto_fix_delete, self.purge_conf)
                    self.deleting = True
            else:
                try:
                    self.install_list.append(DebPackage(filename, self.cache))
                except apt_pkg.Error as e:
                    print(str(e))

    def run(self):
        if self.deleting:
            print('kxfedlog ' + 'Removing packages')
            print('kxfedmsg ' + 'Removing packages')
            sys.stdout.flush()
            self.cache.commit(None, install_progress=self.delprogress)
        if self.install_list:
            try:
                for each in self.install_list:
                    if each.check():
                        if each.check_breaks_existing_packages():
                            if each.check_conflicts():
                                each.install(self.instprogress)
                            else:
                                raise apt_pkg.Error("conflicts")
                        else:
                            raise apt_pkg.Error("breaks existing")
                    else:
                        #raise apt_pkg.Error
                        print("kxfedmsg missing dependencies, check messages")
                        print("kxfedlog + check fails missing dependencies \n" + str(each.missing_deps))
                        sys.stdout.flush()
                        if self.auto_fix_install:
                            for p in each.missing_deps:
                                pkg = self.cache[p]
                                pkg.mark_install()
                            self.cache.commit(install_progress=self.instprogress)
                            each.install(self.instprogress)
                        break
            except apt_pkg.Error as e:
                print('kxfedexcept', str(e).replace('\n', ' '))
                sys.stdout.flush()
                self.stop = True
                return
        return


if __name__ == '__main__':
    deb_install = DebInstall()
    deb_install.prepare()
    tp = thread_pool(10)
    result = tp.apply_async(deb_install.run)
    try:
        while not result.ready():
            if deb_install.stop:
                tp.terminate()
                install_rpms = None
                print("kxfedlog ended in Main")
                sys.stdout.flush()
                break
            nextline = sys.stdin.readline()
            sys.stdin.flush()
            if 'cancel' in nextline:
                deb_install.stop = True
    except Exception as e:
        print('kxfedexcept exception caught in __main__: ' + str(e))
        sys.exit(1)
    sys.exit(0)
