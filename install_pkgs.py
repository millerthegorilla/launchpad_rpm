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

    @dbus.service.method("uk.co.jerlesey.kxfed.InstallPkgs",
                         in_signature='s',
                         out_signature='',
                         sender_keyword='sender')
    def install(self, lp_team_web_address, sender):
        bob = sender
        # get list of packages to be installed from cfg, using pop to delete
        dave = os.geteuid()
        try:
            for ppa in self.cfg['tobeinstalled']:
                print('hello')
                for pkgid in self.cfg['tobeinstalled'][ppa]:
                    if ppa not in self.cfg['installing']:
                        self.cfg['downloading'][ppa] = {}
                    pkg = self.cfg['tobeinstalled'][ppa].pop(pkgid)
                    self.cfg['downloading'][ppa][pkgid] = pkg
                    debs_dir = self.cfg['debs_dir']
                    rpms_dir = self.cfg['rpms_dir']
                    self._thread_pool.apply_async(self.__get_deb_links_and_download__,
                                                  (ppa,
                                                   pkg,
                                                   debs_dir,
                                                   rpms_dir,
                                                   str(lp_team_web_address),))
        except Exception as e:
            print(e)
        #self.progress_adjusted.emit(0, 0)

    def __get_deb_links_and_download__(self, ppa, pkg, debs_dir, rpms_dir, lp_team_web_address):
        # threaded function called from install_packages
        try:
            html = requests.get(lp_team_web_address
                                + '/+archive/ubuntu/'
                                + ppa
                                + '/+build/' + pkg['build_link'].rsplit('/', 1)[-1])
            links = BeautifulSoup(html.content, 'lxml').find_all('a',
                                                                 href=re.compile(r''
                                                                                 + pkg['name']
                                                                                 + r'(.*?)(all|amd64\.deb)'))
            pkg['deb_link'] = links
            for link in links:
                # TODO try os path basename etc out of interest
                fn = link['href'].rsplit('/', 1)[-1]
                fp = debs_dir + splitext(fn)[0]
                with open(fp, "wb+") as f:
                    response = requests.get(link['href'], stream=True)
                    total_length = response.headers.get('content-length')

                    if total_length is None:  # no content length header
                        f.write(response.content)
                    else:
                        total_length = int(total_length)
                        for data in response.iter_content(chunk_size=1024):
                            f.write(data)
                            self.progress_adjusted(len(data), total_length)
                            total_length = 0
                # build_rpms.sh working_dir deb_filepath filename rpms_dir arch
                result = self._mp_pool.apply_async(subprocess.check_output,
                                                   (['/bin/bash',
                                                     '/home/james/Src/kxfed/build_rpms.sh',
                                                     debs_dir,
                                                     fp,
                                                     fn,
                                                     rpms_dir,
                                                     'amd64'],))
                logging.log(logging.DEBUG, result.get())

                # gi.repository.Gtk.main_quit()
                # exit(1)

        except Exception as e:
            print(e)
        # except (requests.HTTPError, subprocess.CalledProcessError) as e:
        #     if e is subprocess.CalledProcessError:
        #         logging.log(logging.ERROR, e.output)
        #         print("!" + e.stderror)
        #         # self.exception.emit(e.stderror)
        #
        #         logging.log(logging.ERROR, traceback.format_exc())
        #     else:
        #         print("!" + e.stderror)
        # bob = u'hello from get debs : ppa = ' + ppa + ' pkg = ' + pkg + ' debs_dir = ' + debs_dir + ' rpms_dir = ' + rpms_dir
        # return bob

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
        session_bus_name = dbus.service.BusName("uk.co.jerlesey.kxfed.InstallPkgs", bus=session_bus, do_not_queue=True)
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

