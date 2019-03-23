#!/usr/bin/python3

import rpm
import os
from kfconf import cfg


class InstallRpms:
    def __init__(self):
        self._rpmtsCallback_fd = None
        unresolved_deps = None
        ts = rpm.TransactionSet()
        try:
            for ppa in cfg['installing']:
                for pkg in cfg['installing'][ppa]:
                    with open(cfg['installing'][ppa][pkg]['rpm_path'], 'rb') as headerfile:
                        h = ts.hdrFromFdno(headerfile)
                        ts.addInstall(h, cfg['installing'][ppa][pkg]['rpm_path'], 'u')

            unresolved_deps = ts.check()
        except Exception as e:
            print('klxfedexcept Error whilst installing packages. line 19 of install_rpms', str(e))
            print('kxfedmsg Error installing packages, see messages')

        if unresolved_deps:
            print("kxfedlog Unresolved Dependencies:")
            for dep_failure in unresolved_deps:
                print('kxfedlog', str(dep_failure))
            print("kxfedmsg ERROR - packages have unmet dependencies, see messages")
        else:
            try:
                ts.order()
                ts.setVSFlags(-1)   # TODO necessary?
                print("kxfedlog This will install:")
                for te in ts:
                    print("kxfedlog %s-%s-%s" % (te.N(), te.V(), te.R()))
            except Exception as e:
                print('kxfedexcept Error whilst installing packages. line 35 of install_rpms', str(e))
                print("kxfedmsg Error installing packages, see messages")

        ts.run(self.run_callback, ts)

    def run_callback(self, reason, amount, total, key, client_data=None):
        if self.cancelled:
            rpm.TransactionSet(client_data).clear()

        if reason == rpm.RPMCALLBACK_INST_OPEN_FILE:
            print("kxfedlog Opening file. ", reason, amount, total, key, client_data)
            self._rpmtsCallback_fd = os.open(key, os.O_RDONLY)
            return self._rpmtsCallback_fd
        elif reason == rpm.RPMCALLBACK_INST_CLOSE_FILE:
            print("kxfedlog Closing file. ", reason, amount, total, key, client_data)
            os.close(self._rpmtsCallback_fd)
        elif reason == rpm.RPMCALLBACK_INST_START:
            print('kxfedmsg Installing', key)
        elif reason == rpm.RPMCALLBACK_INST_PROGRESS:
            print('kxfedprogress ', amount, total)
        elif reason == rpm.RPMCALLBACK_TRANS_PROGRESS:
            print('kxfedtransprogress', amount, total)
        elif reason == rpm.RPMCALLBACK_TRANS_STOP:
            print('kxfedtransprogress', 0, 0)
            exit(0)


if __name__ == '__main__':
    install_rpms = InstallRpms()
