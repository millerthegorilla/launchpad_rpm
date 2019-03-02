#!/usr/bin/python3
import logging
import re
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as thread_pool
from multiprocessing import Pool as mp_pool
from kfconf import cfg
import requests
import subprocess
import traceback
import threading
from os.path import splitext
from configobj import ConfigObj
from pathlib import Path
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import gi
from gi.repository import GLib
import os

CONFIG_DIR = '.config/kxfed/'
CONFIG_FILE = 'kxfed.cfg'


class PkgException(dbus.DBusException):
    _dbus_error_name = "uk.co.jerlesey.kxfed.PkgException"


class InstallPkgs(dbus.service.Object):
    def __init__(self, bus_name):
        try:
            super().__init__(bus_name, "/InstallPkgs")
        except dbus.DBusException:
            raise PkgException("Exception in install pkgs")
        self._thread_pool = thread_pool(10)
        self._mp_pool = mp_pool(10)
        self._result = None
        self._lock = threading.Lock()
        config_dir = str(Path.home()) + '/' + CONFIG_DIR
        self.cfg = ConfigObj(config_dir + CONFIG_FILE)

    @dbus.service.signal("uk.co.jerlesey.kxfed.InstallPkgs", signature='xx')
    def progress_adjusted(self, cur_len, total_len):
        # The signal is emitted when this method exits
        # You can have code here if you wish
        pass


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    mainloop = GLib.MainLoop()
    dbus.mainloop.glib.threads_init()

    try:
        session_bus = dbus.SessionBus()
        session_bus_name = dbus.service.BusName("uk.co.jerlesey.kxfed.Signal", bus=session_bus, do_not_queue=True)
    except dbus.exceptions.NameExistsException:
        print("service is already running")
        sys.exit(1)
    except dbus.exceptions.DBusException as e:
        print(str(e))


    try:
        object = InstallPkgs(session_bus_name)
        mainloop.run()
    except KeyboardInterrupt:
        print("keyboard interrupt received")
    except Exception as e:
        print("unhandled exception occurred:")
    finally:
        mainloop.quit()

