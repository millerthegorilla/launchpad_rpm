#!/usr/bin/python
# Upgrades packages passed on the command line.
# Usage:
# python rpmupgrade.py rpm_file1.rpm rpm_file2.rpm ...
#

import os
import sys
from collections import OrderedDict
import rpm

# Global file descriptor for the callback.
fdnos = OrderedDict()
action = 'installing'


def run_callback(reason, amount, total, key, client_data):
    header, path = key
    global fdnos
    if reason == rpm.RPMCALLBACK_INST_OPEN_FILE:
        print("kxfedlog Opening file. ", path, client_data)
        print("kxfedmsg Opening file. ", path, client_data)
        nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
        fdnos[nvr] = os.open(path, os.O_RDONLY)
        return fdnos[nvr]
    elif reason == rpm.RPMCALLBACK_INST_CLOSE_FILE:
        print("kxfedlog Closing file. ", path, client_data)
        print("kxfedmsg Closing file. ", path, client_data)
        nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
        os.close(fdnos[nvr])
    elif reason == rpm.RPMCALLBACK_INST_START:
        print('kxfedlog Installing', header['NAME'])
        print('kxfedmsg Installing', header['NAME'])
    elif reason == rpm.RPMCALLBACK_INST_PROGRESS:
        print('kxfedprogress ', amount, total)
    elif reason == rpm.RPMCALLBACK_INST_STOP:
        print('kxfedinstalled', header['NAME'])
    elif reason == rpm.RPMCALLBACK_UNINST_START:
        print('kxfedlog Uninstalling', header['NAME'])
        print('kxfedmsg Uninstalling', header['NAME'])
    elif reason == rpm.RPMCALLBACK_UNINST_PROGRESS:
        print('kxfedprogress ', amount, total)
    elif reason == rpm.RPMCALLBACK_UNINST_STOP:
        print('kxfeduninstalled', key)
    elif reason == rpm.RPMCALLBACK_TRANS_START:
        nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
        keys = list(fdnos.keys())
        amount = keys.index(nvr)
        total = len(fdnos)
        print('kxfedtransprogress', amount, total)
    elif reason == rpm.RPMCALLBACK_TRANS_PROGRESS:
        nvr = '%s-%s-%s' % (header['name'], header['version'], header['release'])
        keys = list(fdnos.keys())
        amount = keys.index(nvr)
        total = len(fdnos)
        print('kxfedtransprogress', amount, total)
    elif reason == rpm.RPMCALLBACK_TRANS_STOP:
        # print('kxfedtransprogress', 0, 0)
        print('kxfedstop')
    elif reason == rpm.RPMCALLBACK_VERIFY_START:
        print('kxfedlog Start Verify', header['NAME'])
    elif reason == rpm.RPMCALLBACK_VERIFY_PROGRESS:
        print('kxfedlog Progress Verify', header['NAME'])
    elif reason == rpm.RPMCALLBACK_VERIFY_STOP:
        print('kxfedlog Stop Verify', header['NAME'])
    elif reason == rpm.RPMCALLBACK_SCRIPT_START:
        pass
    elif reason == rpm.RPMCALLBACK_SCRIPT_STOP:
        pass
    elif reason == rpm.RPMCALLBACK_CPIO_ERROR:
        print('kxfedexcept Error getting package data')
    else:
        print('kxfedlog Unhandled Error!', reason)


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

    print("kxfedmsg", name, version, release, reason, required_name, " which is ", filetype)
    print("kxfedlog", name, version, release, reason, required_name, " which is ", filetype)


def readRpmHeader(ts, filename):
    """ Read an rpm header. """
    fd = os.open(filename, os.O_RDONLY)
    try:
        h = ts.hdrFromFdno(fd)
    finally:
        os.close(fd)
    return h


ts = rpm.TransactionSet()


# Set to not verify DSA signatures.
ts.setVSFlags(-1)

for filename in sys.argv[2:]:
    if filename == 'uninstalling':
        ts.addErase(filename)
    else:
        filepath = sys.argv[1] + filename
        h = readRpmHeader(ts, filepath)
        print("kxfedlog Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
        print("kxfedmsg Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
        ts.addInstall(h, (h, filepath), 'i')

unresolved_dependencies = ts.check(check_callback)

if not unresolved_dependencies:
    ts.order()

    print("kxfedmsg This upgrade will install:")
    print("kxfedlog This upgrade will install:")
    for te in ts:
        print("kxfedmsg %s-%s-%s" % (te.NEVR(), te.V(), te.R()))
        print("kxfedlog %s-%s-%s" % (te.NEVR(), te.V(), te.R()))

    print("kxfedmsg Running transaction (final step)...")
    ts.run(run_callback, 1)
else:
    print("Error: Unresolved dependencies, transaction failed.")
    print('kxfedlog', unresolved_dependencies)
    print('kxfedmsg Unresolved Dependencies.  Check Messages')
