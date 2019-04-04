#!/usr/bin/python
# -*- coding: utf-8 -*-
# Upgrades packages passed on the command line.
# Usage:
# python rpmupgrade.py rpm_file1.rpm rpm_file2.rpm ...
#

import sys
from collections import OrderedDict
import rpm
import os
from multiprocessing.dummy import Pool as thread_pool


class InstallRpms:

    def __init__(self):
        self.stop = False
        self.fdnos = OrderedDict()
        self.ts = rpm.TransactionSet()
        print("kxfedlog Transaction root is ", self.ts.rootDir)
        print("kxfedlog Transaction Id = ", self.ts.tid)

        # Set to not verify DSA signatures.
        self.ts.setVSFlags(-1)

    def action(self):
        for filename in sys.argv[2:]:
            if "uninstalling" in filename:
                self.ts.addErase(filename.lstrip('uninstalling'))
            else:
                filepath = sys.argv[1] + filename
                h = self.read_rpm_header(self.ts, filepath)
                print("kxfedlog Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
                print("kxfedmsg Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
                self.ts.addInstall(h, (h, filepath), 'i')

        unresolved_dependencies = self.ts.check()

        if unresolved_dependencies:
            self.unresolved(self.ts, unresolved_dependencies)
        elif not unresolved_dependencies:
            self.ts.order()

            print("kxfedmsg This upgrade will install:")
            print("kxfedlog This upgrade will install:")
            for te in self.ts:
                print("kxfedmsg %s-%s-%s" % (te.NEVR(), te.V(), te.R()))
                print("kxfedlog %s-%s-%s" % (te.NEVR(), te.V(), te.R()))

            print("kxfedmsg Running transaction (final step)...")
            problems = self.ts.run(self.run_callback, self.ts.tid)
            if problems:
                for problem in problems:
                    print("kxfedmsg", problem[0])
                    print("kxfedlog", problem[0])
        else:
            print("Error: Unresolved dependencies, transaction failed.")
            print("kxfedlog", unresolved_dependencies)
            print("kxfedmsg Unresolved Dependencies.  Check Messages")
        sys.stdout.flush()

    def run_callback(self, reason, amount, total, key, client_data):
        if key is not None and self.stop is False:
            if type(key) is not tuple:
                return
            else:
                header, path = key
                if reason == rpm.RPMCALLBACK_INST_OPEN_FILE:
                    print("kxfedlog", client_data, " Opening file. ", path, header['NAME'].decode('utf-8'))
                    print("kxfedmsg", client_data, " Opening file. ", path, header['NAME'].decode('utf-8'))
                    nvr = '%s-%s-%s' % (header['NAME'].decode('utf-8'),
                                        header['VERSION'].decode('utf-8'),
                                        header['RELEASE'].decode('utf-8'))
                    self.fdnos[nvr] = os.open(path, os.O_RDONLY)
                    return self.fdnos[nvr]
                elif reason == rpm.RPMCALLBACK_INST_CLOSE_FILE:
                    print("kxfedlog", client_data, " Closing file. ", path, header['NAME'].decode('utf-8'))
                    print("kxfedmsg", client_data, " Closing file. ", path, header['NAME'].decode('utf-8'))
                    nvr = '%s-%s-%s' % (header['NAME'].decode('utf-8'),
                                        header['VERSION'].decode('utf-8'),
                                        header['RELEASE'].decode('utf-8'))
                    os.close(self.fdnos[nvr])
                elif reason == rpm.RPMCALLBACK_INST_START:
                    print("kxfedlog", client_data, " Installing", header['NAME'].decode('utf-8'))
                    print("kxfedmsg", client_data, " Installing", header['NAME'].decode('utf-8'))
                elif reason == rpm.RPMCALLBACK_INST_PROGRESS:
                    print("kxfedprogress ", amount, total)
                elif reason == rpm.RPMCALLBACK_INST_STOP:
                    print("kxfedinstalled", client_data, header['NAME'].decode('utf-8'))
                elif reason == rpm.RPMCALLBACK_UNINST_START:
                    print("kxfedlog", client_data, " Uninstalling", header['NAME'].decode('utf-8'))
                    print("kxfedmsg", client_data, " Uninstalling", header['NAME'].decode('utf-8'))
                elif reason == rpm.RPMCALLBACK_UNINST_PROGRESS:
                    print("kxfedprogress", amount, total)
                elif reason == rpm.RPMCALLBACK_UNINST_STOP:
                    print("kxfeduninstalled", client_data, " Uninstalled ", header['NAME'].decode('utf-8'))
                elif reason == rpm.RPMCALLBACK_TRANS_START:
                    nvr = '%s-%s-%s' % (header['NAME'].decode('utf-8'),
                                        header['version'].decode('utf-8'),
                                        header['release'].decode('utf-8'))
                    keys = list(self.fdnos.keys())
                    amount = keys.index(nvr)
                    total = len(self.fdnos)
                    print("kxfedtransprogress", amount, total)
                    print("kxfedlog", client_data, " Transaction Progress Started: ", amount, total)
                elif reason == rpm.RPMCALLBACK_TRANS_PROGRESS:
                    nvr = '%s-%s-%s' % (header['NAME'].decode('utf-8'),
                                        header['version'].decode('utf-8'),
                                        header['release'].decode('utf-8'))
                    keys = list(self.fdnos.keys())
                    amount = keys.index(nvr)
                    total = len(self.fdnos)
                    print("kxfedtransprogress", amount, total)
                    print("kxfedlog", client_data, " Transaction Progress Continues: ", amount, total)
                elif reason == rpm.RPMCALLBACK_TRANS_STOP:
                    print("kxfedstop", client_data)
                elif reason == rpm.RPMCALLBACK_VERIFY_START:
                    print("kxfedlog", client_data, " Start Verify", header['NAME'].decode('utf-8'))
                elif reason == rpm.RPMCALLBACK_VERIFY_PROGRESS:
                    print("kxfedlog", client_data, " Progress Verify", header['NAME'].decode('utf-8'))
                elif reason == rpm.RPMCALLBACK_VERIFY_STOP:
                    print('kxfedlog", client_data, " Stop Verify', header['NAME'].decode('utf-8'))
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
    def unresolved(ts, unresolved_dependencies):
        for tup in unresolved_dependencies:
            name, version, release = tup[0]
            required_name, required_version = tup[1]
            if required_version is None:
                filetype = "a library "
            else:
                filetype = "an application "

            if tup[4] == rpm.RPMDEP_SENSE_CONFLICTS:
                reason = "conflicts "
            else:
                reason = "requires "

            print("kxfedmsg", str(ts.tid), " Dependency issue : ",
                  name, version, release, " ",
                  reason, " ", required_name,
                  " which is ", filetype,
                  " A suggested Package is ", tup[3])
            print("kxfedlog", str(ts.tid), " Dependency issue : ",
                  name, version, release, " ",
                  reason, " ", required_name,
                  " which is ", filetype,
                  " A suggested Package is ", tup[3])
            sys.stdout.flush()

    @staticmethod
    def read_rpm_header(ts, filename):
        """ Read an rpm header. """
        with open(filename, 'r') as fd:
            try:
                h = ts.hdrFromFdno(fd)
            except Exception as e:
                print("kxfedexcept ", str(e))
                sys.stdout.flush()
        return h


if __name__ == '__main__':
    install_rpms = InstallRpms()
    tp = thread_pool(10)
    result = tp.apply_async(install_rpms.action)
    while not result.ready():
        if install_rpms.stop:
            tp.close()
            tp.terminate()
            install_rpms = None
            print("kxfedlog ended in Main")
            sys.stdout.flush()
            break
        nextline = sys.stdin.readline().decode('utf-8')
        if 'cancel' in nextline:
            install_rpms.stop = True
        # for line in fileinput.input(openhook=fileinput.hook_encoded("utf-8")):
        #     if "cancel" in line.encode('utf-8').decode():
        #         install_rpms.stop = True
    sys.exit(0)
