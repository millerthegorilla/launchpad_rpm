# config.py
import os, sys
from pathlib import Path
from configobj import ConfigObj
from dogpile.cache import make_region
from PyQt5.QtCore import Qt
from threading import RLock

# constants
CONFIG_DIR = ".config/kxfed/"
CONFIG_FILE = "kxfed.cfg"
CACHE_FILE = "kxfed.cache.db"
TVITEM_ROLE = Qt.UserRole + 1

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
    cfg['cache']['initiated']              = {}
    cfg['pkg_states']                      = {}
    cfg['pkg_states']['tobeinstalled']     = {}
    cfg['pkg_states']['tobeuninstalled']   = {}
    cfg['pkg_states']['downloading']       = {}
    cfg['pkg_states']['converting']        = {}
    cfg['pkg_states']['installing']        = {}
    cfg['pkg_states']['uninstalling']      = {}
    cfg['pkg_states']['installed']         = {}
    cfg['tmp_dir']                         = tmp_dir
    cfg['debs']                            = {}
    cfg['debs_dir']                        = debs_dir
    cfg['log_name']                        = "kxfed.log"
    cfg['rpms_dir']                        = rpms_dir
    cfg['arch']                            = "amd64"
    cfg['download']                        = "True"
    cfg['convert']                         = "True"
    cfg['install']                         = "True"
    cfg['log_file_path']                   = tmp_dir + cfg["log_name"]
else:
    cfg = ConfigObj(config_dir + CONFIG_FILE)


def delete_ppa_if_empty(section, ppa):
    if not cfg[section][ppa]:
        cfg[section].pop(ppa)


def add_item_to_section(section, pkg):
    if pkg.ppa not in cfg['pkg_states'][section]:
        cfg['pkg_states'][section][pkg.ppa] = {}
    if pkg.id not in cfg['pkg_states'][section][pkg.ppa]:
        cfg['pkg_states'][section][pkg.ppa][pkg.id] = {}
        cfg['pkg_states'][section][pkg.ppa][pkg.id]['id'] = pkg.id
        cfg['pkg_states'][section][pkg.ppa][pkg.id]['name'] = pkg.name
        cfg['pkg_states'][section][pkg.ppa][pkg.id]['version'] = pkg.version
        cfg['pkg_states'][section][pkg.ppa][pkg.id]['deb_link'] = pkg.deb_link
        cfg['pkg_states'][section][pkg.ppa][pkg.id]['deb_paths'] = str(pkg.deb_paths)
        cfg['pkg_states'][section][pkg.ppa][pkg.id]['rpm_path'] = pkg.rpm_path
        cfg['pkg_states'][section][pkg.ppa][pkg.id]['build_link'] = pkg.build_link


cache = make_region().configure(
            backend=cfg['cache']['backend'],
            expiration_time=int(cfg['cache']['expiration_time']),
            arguments={'filename': cfg['cache']['arguments']['filename']})

cfg._lock = RLock()
cfg.delete_ppa_if_empty = delete_ppa_if_empty
cfg.add_item_to_section = add_item_to_section

__this__.cfg = cfg
__this__.cache = cache
__this__.pkg_states = cfg['pkg_states']
