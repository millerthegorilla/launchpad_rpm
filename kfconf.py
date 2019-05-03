#!/usr/bin/python3
# config.py
import os
import sys
from pathlib import Path
from threading import RLock

from configobj import ConfigObj
from dogpile.cache import make_region
from tvitem import TVItem
import distro
if 'Fedora' in distro.linux_distribution():
    from rpm import TransactionSet
    DISTRO_TYPE = 'rpm'
else:
    import apt
    APT_CACHE_FILE = apt.Cache()
    DISTRO_TYPE = 'deb'
# TODO when the program installs the line below must be added to ~/.rpmmacros
# %_topdir /home/data/rpmbuild

# constants
CONFIG_DIR = ".config/kxfed/"
CONFIG_FILE = "kxfed.cfg"
CACHE_FILE = "kxfed.cache.db"
SCRIPT_PATH = "/home/james/Src/launchpad_rpm/"
ENDED_ERR = 0
ENDED_SUCC = 1
ENDED_CANCEL = 2

__this__ = sys.modules[__name__]

config_dir = str(Path.home()) + "/" + CONFIG_DIR
tmp_dir = str(Path.home()) + "/.local/share/kxfed/"
debs_dir = tmp_dir + "debs/"
rpms_dir = tmp_dir + "rpms/"


def change_tmp_dir(tmpdir):
    cfg[tmp_dir] = tmpdir
    cfg[debs_dir] = tmpdir + "debs/"
    cfg[rpms_dir] = tmpdir + "rpms/"


def mkpath(path):
    if not Path(path).exists():
        Path(path).mkdir(parents=True, exist_ok=True)


paths = [config_dir, tmp_dir, debs_dir, rpms_dir]
for path in paths:
    mkpath(path)

if not os.path.exists(config_dir + CONFIG_FILE):
    cfg = ConfigObj()
    cfg['config'] = {}
    cfg['config']['dir'] = config_dir
    cfg['config']['filename'] = CONFIG_FILE
    cfg['cache'] = {}
    cfg['cache']['filename'] = CACHE_FILE
    cfg['cache']['backend'] = "dogpile.cache.dbm"
    cfg['cache']['enabled'] = "True"
    cfg['cache']['expiration_time'] = "604800"
    cfg['cache']['arguments'] = {}
    cfg['cache']['arguments']['filename'] = config_dir + CACHE_FILE
    cfg['cache']['initiated'] = {}
    cfg['distro_type'] = DISTRO_TYPE
    cfg['pkg_states'] = {}
    cfg['pkg_states']['tobeinstalled'] = {}
    cfg['pkg_states']['tobeuninstalled'] = {}
    cfg['pkg_states']['downloading'] = {}
    cfg['pkg_states']['converting'] = {}
    cfg['pkg_states']['installing'] = {}
    cfg['pkg_states']['uninstalling'] = {}
    cfg['pkg_states']['installed'] = {}
    cfg['pkg_states']['failed_downloading'] = {}
    cfg['pkg_states']['failed_converting'] = {}
    cfg['pkg_states']['failed_installing'] = {}
    cfg['pkg_states']['failed_uninstalling'] = {}
    cfg['tmp_dir'] = tmp_dir
    cfg['debs'] = {}
    cfg['debs_dir'] = debs_dir
    cfg['log_name'] = "kxfed.log"
    cfg['rpms_dir'] = rpms_dir
    cfg['arch'] = "amd64"
    cfg['download'] = "True"
    cfg['convert'] = "True"
    cfg['install'] = "True"
    cfg['uninstall'] = "True"
    cfg['delete_converted'] = "True"
    cfg['delete_downloaded'] = "True"
    cfg['log_file_path'] = tmp_dir + cfg["log_name"]
else:
    cfg = ConfigObj(config_dir + CONFIG_FILE)


def delete_ppa_if_empty(section, ppa):
    """section is string, ppa is string"""
    if ppa in cfg['pkg_states'][section]:
        if not cfg['pkg_states'][section][ppa]:  # if ppa is empty
            cfg['pkg_states'][section].pop(ppa)


def clean_section(sections):
    # sections is a list of section objects
    if type(sections) is not list:
        sections = [sections]
    for section in sections:
        if type(section) is str:
            section = cfg['pkg_states'][section]
        for ppa in section:
            delete_ppa_if_empty(section.name, ppa)


def add_item_to_section(section, pkg):
    """section is a string name of section
       pkg is of type tvitem or a configobj section"""
    if type(pkg) is TVItem:
        if pkg.ppa not in cfg['pkg_states'][section]:
            cfg['pkg_states'][section][pkg.ppa] = {}
        if pkg.id not in cfg['pkg_states'][section][pkg.ppa]:
            cfg['pkg_states'][section][pkg.ppa][pkg.id] = {}
            cfg['pkg_states'][section][pkg.ppa][pkg.id]['id'] = pkg.id
            cfg['pkg_states'][section][pkg.ppa][pkg.id]['name'] = pkg.name
            cfg['pkg_states'][section][pkg.ppa][pkg.id]['version'] = pkg.version
            cfg['pkg_states'][section][pkg.ppa][pkg.id]['deb_link'] = pkg.deb_link
            cfg['pkg_states'][section][pkg.ppa][pkg.id]['deb_path'] = pkg.deb_path
            cfg['pkg_states'][section][pkg.ppa][pkg.id]['rpm_path'] = pkg.rpm_path
            cfg['pkg_states'][section][pkg.ppa][pkg.id]['build_link'] = pkg.build_link
            return True
        else:
            return False
    else:
        if pkg.parent.name not in cfg['pkg_states'][section]:
            cfg['pkg_states'][section][pkg.parent.name] = {}
        if pkg['id'] not in cfg['pkg_states'][section][pkg.parent.name]:
            cfg['pkg_states'][section][pkg.parent.name][pkg['id']] = pkg
            return True
        else:
            return False


def has_pending(section):
    if cfg['pkg_states'][section]:
        for ppa in cfg['pkg_states'][section]:
            if cfg['pkg_states'][section][ppa]:
                return True
    return False


def pkg_search(sections, search_value):
    """sections is a list of strings - names of sections - to search
       search value is content string"""
    for section in sections:
        for ppa in cfg['pkg_states'][section]:
            for pkgid in cfg['pkg_states'][section][ppa]:
                if search_value in cfg['pkg_states'][section][ppa][pkgid].dict().values():
                    return cfg['pkg_states'][section][ppa][pkgid]
    return False


def check_installed(name):
    if cfg['distro_type'] == 'rpm':
        return True if len(TransactionSet().dbMatch('name', name)) else False
    else:
        try:
            p = APT_CACHE_FILE[name]
            if hasattr(p, 'isInstalled'):
                return True if p.isInstalled else False
            else:
                return False
        except KeyError as e:
            return False


cache = make_region().configure(
    backend=cfg['cache']['backend'],
    expiration_time=int(cfg['cache']['expiration_time']),
    arguments={'filename':cfg['cache']['arguments']['filename']})

cfg._lock = RLock()
cfg.delete_ppa_if_empty = delete_ppa_if_empty
cfg.add_item_to_section = add_item_to_section

__this__.cfg = cfg
__this__.cache = cache
__this__.pkg_states = cfg['pkg_states']