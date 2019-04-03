#!/usr/bin/python
# Upgrades packages passed on the command line.
# Usage:
# python rpmupgrade.py rpm_file1.rpm rpm_file2.rpm ...
#

import os
import sys
from collections import OrderedDict
import rpm
import fileinput


class InstallRpms:

    def __init__(self):
        self.stop = False
        self.fdnos = OrderedDict()
        ts = rpm.TransactionSet()
        print("kxfedlog Transaction root is ", ts.rootDir())
        print("kxfedlog Transaction Id = ", ts.tid)

        # Set to not verify DSA signatures.
        ts.setVSFlags(-1)

        for filename in sys.argv[2:]:
            if filename == 'uninstalling':
                ts.addErase(filename)
            else:
                filepath = sys.argv[1] + filename
                h = self.read_rpm_header(ts, filepath)
                print("kxfedlog Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
                print("kxfedmsg Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
                ts.addInstall(h, (h, filepath), 'i')

        unresolved_dependencies = ts.check(self.check_callback)

        if not unresolved_dependencies:
            ts.order()

            print("kxfedmsg This upgrade will install:")
            print("kxfedlog This upgrade will install:")
            for te in ts:
                print("kxfedmsg %s-%s-%s" % (te.NEVR(), te.V(), te.R()))
                print("kxfedlog %s-%s-%s" % (te.NEVR(), te.V(), te.R()))

            print("kxfedmsg Running transaction (final step)...")
            ts.run(self.run_callback, ts.tid)
        else:
            print("Error: Unresolved dependencies, transaction failed.")
            print('kxfedlog', unresolved_dependencies)
            print('kxfedmsg Unresolved Dependencies.  Check Messages')

    def run_callback(self, reason, amount, total, key, client_data):
        header, path = key
        if reason == rpm.RPMCALLBACK_INST_OPEN_FILE:
            print("kxfedlog", client_data, " Opening file. ", path, header[rpm.RPMTAG_NAME])
            print("kxfedmsg", client_data, " Opening file. ", path, header[rpm.RPMTAG_NAME])
            nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
            self.fdnos[nvr] = os.open(path, os.O_RDONLY)
            return self.fdnos[nvr]
        elif reason == rpm.RPMCALLBACK_INST_CLOSE_FILE:
            print("kxfedlog", client_data, " Closing file. ", path, header[rpm.RPMTAG_NAME])
            print("kxfedmsg", client_data, " Closing file. ", path, header[rpm.RPMTAG_NAME])
            nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
            os.close(self.fdnos[nvr])
        elif reason == rpm.RPMCALLBACK_INST_START:
            print("kxfedlog", client_data, " Installing", header['NAME'])
            print("kxfedmsg", client_data, " Installing", header['NAME'])
        elif reason == rpm.RPMCALLBACK_INST_PROGRESS:
            print("kxfedprogress ", amount, total)
        elif reason == rpm.RPMCALLBACK_INST_STOP:
            print("kxfedinstalled", client_data, header['NAME'])
        elif reason == rpm.RPMCALLBACK_UNINST_START:
            print("kxfedlog", client_data, " Uninstalling", header['NAME'])
            print("kxfedmsg", client_data, " Uninstalling", header['NAME'])
        elif reason == rpm.RPMCALLBACK_UNINST_PROGRESS:
            print("kxfedprogress", amount, total)
        elif reason == rpm.RPMCALLBACK_UNINST_STOP:
            print("kxfeduninstalled", client_data, " Uninstalled ", header['NAME'])
        elif reason == rpm.RPMCALLBACK_TRANS_START:
            nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
            keys = list(self.fdnos.keys())
            amount = keys.index(nvr)
            total = len(self.fdnos)
            print("kxfedtransprogress", amount, total)
            print("kxfedlog", client_data, " Transaction Progress Started: ", amount, total)
        elif reason == rpm.RPMCALLBACK_TRANS_PROGRESS:
            nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
            keys = list(self.fdnos.keys())
            amount = keys.index(nvr)
            total = len(self.fdnos)
            print("kxfedtransprogress", amount, total)
            print("kxfedlog", client_data, " Transaction Progress Continues: ", amount, total)
        elif reason == rpm.RPMCALLBACK_TRANS_STOP:
            print("kxfedstop", client_data)
        elif reason == rpm.RPMCALLBACK_VERIFY_START:
            print("kxfedlog", client_data, " Start Verify", header['NAME'])
        elif reason == rpm.RPMCALLBACK_VERIFY_PROGRESS:
            print("kxfedlog", client_data, " Progress Verify", header['NAME'])
        elif reason == rpm.RPMCALLBACK_VERIFY_STOP:
            print('kxfedlog", client_data, " Stop Verify', header['NAME'])
        elif reason == rpm.RPMCALLBACK_SCRIPT_START:
            pass
        elif reason == rpm.RPMCALLBACK_SCRIPT_STOP:
            pass
        elif reason == rpm.RPMCALLBACK_CPIO_ERROR:
            print("kxfedexcept", client_data, " Error getting package data")
        else:
            print("kxfedlog Unhandled Error!", client_data, reason)
        sys.stdout.flush()

    @staticmethod
    def check_callback(nvr, req, needsflags, suggestedpkg, sense):
        name, version, release = nvr
        required_name, required_version = req
        if required_version is None:
            filetype = "a library "
        else:
            filetype = "an application "

        if sense == rpm.RPMSENSE_CONFLICTS:
            reason = "conflicts "
        else:
            reason = "requires "

        print("kxfedmsg", " Dependency issue : ",
              name, version, release, " ",
              reason, " ", required_name,
              " which is ", filetype,
              " A suggested Package is ", suggestedpkg)
        print("kxfedlog", " Dependency issue : ",
              name, version, release, " ",
              reason, " ", required_name,
              " which is ", filetype,
              " A suggested Package is ", suggestedpkg)
        sys.stdout.flush()

    @staticmethod
    def read_rpm_header(ts, filename):
        """ Read an rpm header. """
        with os.open(filename, os.O_RDONLY) as fd:
            try:
                h = ts.hdrFromFdno(fd)
            except Exception as e:
                print("kxfedexcept ", str(e))
                sys.stdout.flush()
        return h


if __name__ == '__main__':
    install_rpms = InstallRpms()
    while 1:
        if install_rpms.stop:
            install_rpms = None
            print("kxfedlog ended in Main")
            break
        for line in fileinput.input():
            if "cancel" in line:
                install_rpms.stop = True
    sys.exit(0)
