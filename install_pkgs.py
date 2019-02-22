#!/usr/bin/python
import logging
import re
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as thread_pool
from multiprocessing import Pool as mp_pool
from kfconf import cfg, cache
import requests
import subprocess
import traceback
import threading
from os.path import splitext
from configobj import ConfigObj
from pathlib import Path

CONFIG_DIR = '.config/kxfed/'
CONFIG_FILE = 'kxfed.cfg'


class InstallPkgs:
    def __init__(self):
        self._thread_pool = thread_pool(10)
        self._mp_pool = mp_pool(10)
        self._result = None
        self._lock = threading.Lock()
        config_dir = str(Path.home()) + '/' + CONFIG_DIR
        self.cfg = ConfigObj(config_dir + CONFIG_FILE)

    def install_pkgs(self):
        # get list of packages to be installed from cfg, using pop to delete
        for ppa in cfg['tobeinstalled']:
            for pkgid in cfg['tobeinstalled'][ppa]:
                if ppa not in cfg['installing']:
                    cfg['downloading'][ppa] = {}
                pkg = cfg['tobeinstalled'][ppa].pop(pkgid)
                cfg['downloading'][ppa][pkgid] = pkg
                debs_dir = cfg['debs_dir']
                rpms_dir = cfg['rpms_dir']
                self._thread_pool.apply_async(self._get_deb_links_and_download,
                                              (ppa,
                                               pkg,
                                               debs_dir,
                                               rpms_dir,))
        #self.progress_adjusted.emit(0, 0)

    def _get_deb_links_and_download(self, ppa, pkg, debs_dir, rpms_dir):
        # threaded function called from install_packages
        try:
            html = requests.get(self._lp_team.web_link
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
                            print(str(len(data)) + ":" + str(total_length))
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

        except (requests.HTTPError, subprocess.CalledProcessError) as e:
            if e is subprocess.CalledProcessError:
                logging.log(logging.ERROR, e.output)
                print("!" + e.stderror)
                # self.exception.emit(e.stderror)

            else:
                logging.log(logging.ERROR, traceback.format_exc())
                print("!" + e.stderror)

                # self.exception.emit(e)


if __name__ == '__main__':
    pkg = InstallPkgs()
    pkg.install_pkgs()
