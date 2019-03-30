#!/usr/bin/python
# Upgrades packages passed on the command line.
# Usage:
# python rpmupgrade.py rpm_file1.rpm rpm_file2.rpm ...
#

import os
import sys

import rpm

# Global file descriptor for the callback.
rpmtsCallback_fd = None
action = 'installing'


def run_callback(reason, amount, total, key, client_data):
    global rpmtsCallback_fd
    if reason == rpm.RPMCALLBACK_INST_OPEN_FILE:
        print("kxfedlog Opening file. ", reason, amount, total, key, client_data)
        rpmtsCallback_fd = os.open(key, os.O_RDONLY)
        return rpmtsCallback_fd
    elif reason == rpm.RPMCALLBACK_INST_CLOSE_FILE:
        print("kxfedlog Closing file. ", reason, amount, total, key, client_data)
        os.close(rpmtsCallback_fd)
    elif reason == rpm.RPMCALLBACK_INST_START:
        print('kxfedmsg Installing', key)
    elif reason == rpm.RPMCALLBACK_INST_PROGRESS:
        print('kxfedprogress ', amount, total)
    elif reason == rpm.RPMCALLBACK_INST_STOP:
        print('kxfedinstalled', key)
    elif reason == rpm.RPMCALLBACK_UNINST_START:
        print('kxfedmsg Uninstalling', key)
    elif reason == rpm.RPMCALLBACK_UNINST_PROGRESS:
        print('kxfedprogress ', amount, total)
    elif reason == rpm.RPMCALLBACK_UNINST_STOP:
        print('kxfeduninstalled', key)
    elif reason == rpm.RPMCALLBACK_TRANS_START:
        print('kxfedtransprogress', amount, total)
    elif reason == rpm.RPMCALLBACK_TRANS_PROGRESS:
        print('kxfedtransprogress', amount, total)
    elif reason == rpm.RPMCALLBACK_TRANS_STOP:
        print('kxfedtransprogress', 0, 0)
        print('kxfedstop')
    elif reason == rpm.RPMCALLBACK_VERIFY_START:
        print('kxfedlog Start Verify', key)
    elif reason == rpm.RPMCALLBACK_VERIFY_PROGRESS:
        print('kxfedlog Progress Verify', key)
    elif reason == rpm.RPMCALLBACK_VERIFY_STOP:
        print('kxfedlog Stop Verify', key)
    elif reason == rpm.RPMCALLBACK_SCRIPT_START:
        pass
    elif reason == rpm.RPMCALLBACK_SCRIPT_STOP:
        pass
    elif reason == rpm.RPMCALLBACK_CPIO_ERROR:
        print('kxfedexcept Error getting package data')
    else:
        print('kxfedlog Unhandled Error!', reason)


def check_callback(ts, TagN, N, EVR, Flags):
    if TagN == rpm.RPMTAG_REQUIRENAME:
        prev = ""
    Nh = None

    if N[0] == '/':
        dbitag = 'basenames'
    else:
        dbitag = 'providename'

    # What do you need to do.
    if EVR:
        print ("Must find package [", N, "-", EVR, "]")
    else:
        print ("Must find file [", N, "]")

    return 1


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
        action = 'uninstalling'
    if action == 'uninstalling':
        ts.addErase(filename)
    else:
        filepath = sys.argv[1] + filename
        h = readRpmHeader(ts, filepath)
        print("kxfedlog Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
        print("kxfedmsg Installing/Upgrading %s-%s-%s" % (h['name'], h['version'], h['release']))
        ts.addInstall(h, filepath, 'i')

unresolved_dependencies = ts.check(check_callback)

if not unresolved_dependencies:
    ts.order()

    print("kxfedmsg This upgrade will install:")
    print("kxfedlog This upgrade will install:")
    for te in ts:
        print("kxfedmsg %s-%s-%s" % (te.N(), te.V(), te.R()))
        print("kxfedlog %s-%s-%s" % (te.N(), te.V(), te.R()))

    print("kxfedmsg Running transaction (final step)...")
    ts.run(run_callback, 1)
else:
    print("Error: Unresolved dependencies, transaction failed.")
    print('kxfedlog', unresolved_dependencies)
    print('kxfedmsg Unresolved Dependencies.  Check Messages')
