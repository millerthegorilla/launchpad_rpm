# config.py
import os, sys
from pathlib import Path
from configobj import ConfigObj
from dogpile.cache import make_region
from PyQt5.QtCore import Qt
from threading import RLock

# constants
CONFIG_DIR = '.config/kxfed/'
CONFIG_FILE = 'kxfed.cfg'
CACHE_FILE = "kxfed.cache.db"
TVITEM_ROLE = Qt.UserRole + 1

__this__ = sys.modules[__name__]

config_dir = str(Path.home()) + '/' + CONFIG_DIR
tmp_dir = str(Path.home()) + '/.local/share/kxfed/'
debs_dir = tmp_dir + 'debs'
rpms_dir = tmp_dir + 'rpms'


def mkpath(path):
    if not Path(path).exists():
        Path(path).mkdir(parents=True, exist_ok=True)


paths = [config_dir, tmp_dir, debs_dir, rpms_dir]
map(mkpath, paths)

if not os.path.exists(config_dir + CONFIG_FILE):
    cfg = ConfigObj()
    cfg['config']                          = {}
    cfg['config']['dir']                   = config_dir
    cfg['config']['filename']              = CONFIG_FILE
    cfg['cache']                           = {}
    cfg['cache']['filename']               = CACHE_FILE
    cfg['cache']['backend']                = "dogpile.cache.dbm"
    cfg['cache']['enabled']                = "True"
    cfg['cache']['expiration_time']        = "604800"
    cfg['cache']['arguments']              = {}
    cfg['cache']['arguments']['filename']  = config_dir + CACHE_FILE
    cfg['installed']                       = {}
    cfg['tobeinstalled']                   = {}
    cfg['tobeuninstalled']                 = {}
    cfg['downloading']                     = {}
    cfg['converting']                      = {}
    cfg['installing']                      = {}
    cfg['tmp_dir']                         = tmp_dir
    cfg['debs']                            = {}
    cfg['debs_dir']                        = debs_dir
    cfg['log']                             = ''
    cfg['rpms_dir']                        = rpms_dir
else:
    cfg = ConfigObj(config_dir + CONFIG_FILE)

cache = make_region().configure(
    backend=cfg['cache']['backend'],
    expiration_time=int(cfg['cache']['expiration_time']),
    arguments={ 'filename' : cfg['cache']['arguments']['filename'] })


def delete_ppa_if_empty(section, ppa):
    if not cfg[section][ppa]:
        cfg[section].pop(ppa)


def add_item_to_section(section, pkg):
    if pkg.ppa not in cfg[section]:
        cfg[section][pkg.ppa] = {}
    if pkg.id not in cfg[section][pkg.ppa]:
        cfg[section][pkg.ppa][pkg.id] = {}
        cfg[section][pkg.ppa][pkg.id]['name'] = pkg.name
        cfg[section][pkg.ppa][pkg.id]['version'] = pkg.version
        cfg[section][pkg.ppa][pkg.id]['deb_link'] = pkg.deb_link
        cfg[section][pkg.ppa][pkg.id]['build_link'] = pkg.build_link


def config_search(section, key, search_key, sect):
    if section[key] == search_key or search_key in section[key]:
        sect.append(section)


cfg._lock = RLock()
cfg.search = config_search
cfg.delete_ppa_if_empty = delete_ppa_if_empty
cfg.add_item_to_section = add_item_to_section

__this__.cfg = cfg
__this__.cache = cache
