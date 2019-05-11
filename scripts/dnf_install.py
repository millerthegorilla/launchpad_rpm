#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from dnf import Base, callback, exceptions
from multiprocessing.dummy import Pool as thread_pool


class Progress(callback.TransactionProgress):
    def __init__(self):
        super().__init__()

    @staticmethod
    def error(message):
        print('kxfedmsg', "There has been a transaction error, please check messages")
        print('kxfedlog', message)
        print('kxfedexcept', message)
        sys.stdout.flush()

    @staticmethod
    def progress(package, action, ti_done, ti_total, ts_done, ts_total):
        if action == callback.PKG_INSTALL:
            if ti_done == 0:
                print('kxfedmsg', package.name, " is being installed.")
                print('kxfedlog', package.name, " is being installed.")
                sys.stdout.flush()
            if ti_done == ti_total:
                print('kxfedinstalled', package.name)
                print('kxfedmsg', package.name, " is being verified.")
                print('kxfedlog', package.name, " is being verified.")
                print('kxfedverify_begin')
                sys.stdout.flush()
        if action == callback.PKG_REMOVE:
            if ti_done == 0:
                print('kxfedmsg', package.name, " is being removed.")
                print('kxfedlog', package.name, " is being removed.")
                sys.stdout.flush()
            if ti_done == ti_total:
                print('kxfeduninstalled', package.name)
                print('kxfedmsg', package.name, " is being verified.")
                print('kxfedlog', package.name, " is being verified.")
                print('kxfedverify_begin')
                sys.stdout.flush()
        if action == callback.PKG_VERIFY:
            print('kxfedmsg', package.name, " is verified.")
            print('kxfedlog', package.name, " is verified.")
            print('kxfedverify_end')
            sys.stdout.flush()
        if action == callback.TRANS_PREPARATION:
            print('kxfedmsg', "Transaction is being prepared")
            print('kxfedlog', "Transaction is being prepared")
            sys.stdout.flush()
        if action == callback.TRANS_POST:
            print('kxfedmsg', "Transaction finished, verification continuing...")
            print('kxfedlog', "Transaction finished, verification continuing...")
            print('kxfedverify_begin')
            sys.stdout.flush()
            ti_done = 0
            ti_total = 0
            ts_done = 0
            ts_total = 0
        print('kxfedprogress', ti_done, ti_total)
        print('kxfedtransprogress', ts_done, ts_total)
        sys.stdout.flush()


class ActionRpms:
    def __init__(self):
        self.stop = False
        self.base = Base()
        self.conf = self.base.conf
        self.conf.cachedir = sys.argv[1]
        self.sack = self.base.fill_sack()
        self.base.resolve()
        self.progress = Progress()

    def action(self):
        for filename in sys.argv[2:]:
            if "uninstalling" in filename:
                name = filename.replace('uninstalling', '')
                print('kxfedmsg Uninstalling ', name)
                sys.stdout.flush()
                q = self.base.sack.query()
                i = q.installed()
                i = i.filter(name=name)
                if len(i):
                    pkg = i[0]
                    self.base.transaction.add_erase(pkg)
                else:
                    print('kxfedexcept', 'Error uninstalling ', name, ' It\'s not installed...')
                    sys.stdout.flush()
            else:
                name = filename
                print('kxfedmsg Installing ', name)
                sys.stdout.flush()
                pkgs = self.base.add_remote_rpms([name])
                self.base.transaction.add_install(pkgs[0])
        try:
            self.base.do_transaction(self.progress)
        except (exceptions.Error, exceptions.TransactionCheckError) as e:
            print('kxfedexcept', str(e).replace('\n', ' '))
            sys.stdout.flush()


if __name__ == '__main__':
    action_rpms = ActionRpms()
    tp = thread_pool(10)
    result = tp.apply_async(action_rpms.action)
    while not result.ready():
        if action_rpms.stop:
            tp.close()
            tp.terminate()
            install_rpms = None
            print("kxfedlog ended in Main")
            sys.stdout.flush()
            break
        nextline = sys.stdin.readline()
        sys.stdin.flush()
        if 'cancel' in nextline:
            action_rpms.stop = True
    sys.exit(0)
