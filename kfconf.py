# config.py
import os, sys
from pathlib import Path
from configobj import ConfigObj
from dogpile.cache import make_region
from PyQt5.QtCore import Qt
CONFIG_DIR = '.config/kxfed/'
CONFIG_FILE = 'kxfed.cfg'
CACHE_FILE = "kxfed.cache.db"
TVITEM_ROLE = Qt.UserRole + 1
RPMS_DIR = 'rpms'

__this__ = sys.modules[__name__]

config_dir = str(Path.home()) + '/' + CONFIG_DIR
if not Path(config_dir).exists():
    Path(config_dir).mkdir(parents=True, exist_ok=True)
tmp_dir = str(Path.home()) + '/.local/share/kxfed/'
if not Path(tmp_dir).exists():
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)


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
    cfg['debs_dir']                        = tmp_dir + 'debs/'
    cfg['log']                             = ''
    cfg['rpms_dir']                        = cfg['debs_dir'] + RPMS_DIR
else:
    cfg = ConfigObj(config_dir + CONFIG_FILE)

cache = make_region().configure(
    backend=cfg['cache']['backend'],
    expiration_time=int(cfg['cache']['expiration_time']),
    arguments={ 'filename' : cfg['cache']['arguments']['filename'] })

__this__.cfg = cfg
__this__.cache = cache