# config.py
import sys, os
from pathlib import Path
import datetime
from configobj import ConfigObj
from dogpile.cache import make_region
CONFIG_DIR = '.config/kxfed/'
CONFIG_FILE = 'kxfed.cfg'

__this__ = sys.modules[__name__]

__this__.cfg = None
__this__.cache = None


# class KFConf:
   # def __init__(self):
        # launchpadlib config - not necessary or move to module level / outer scope
        # useful for deleting in case of uninstall?
home = str(Path.home()) + '/'
lp_cache_dir = home + ".launchpadlib/api.launchpad.net/cache/"
if not os.path.exists(lp_cache_dir):
    os.mkdir(lp_cache_dir, 0o755)

if __this__.cfg is None:
    # also in local function scope. no scope specifier like global is needed
    config_dir = home + CONFIG_DIR
    if not os.path.exists(config_dir):
        os.mkdir(config_dir, 0o755)

    cache_filename = "kxfed.cache.dbm"
    if not os.path.exists(config_dir + CONFIG_FILE):
        __this__.cfg = ConfigObj()
        __this__.cfg['config']                          = {}
        __this__.cfg['config']['dir']                   = config_dir
        __this__.cfg['config']['filename']              = CONFIG_FILE
        __this__.cfg['cache']                           = {}
        __this__.cfg['cache']['filename']               = cache_filename
        __this__.cfg['cache']['backend']                = "dogpile.cache.dbm"
        __this__.cfg['cache']['enabled']                = "True"
        __this__.cfg['cache']['expiration_time']        = "604800"
        __this__.cfg['cache']['arguments']              = {}
        __this__.cfg['cache']['arguments']['filename']  = config_dir + cache_filename
        __this__.cfg['installed']                       = {}
        __this__.cfg['tobeinstalled']                   = {}
        __this__.cfg['tobeuninstalled']                 = {}
    else:
        __this__.cfg = ConfigObj(config_dir + CONFIG_FILE)

if __this__.cache is None:
    # # tree cache built from scratch from the point that the program starts to the point
    # # that it closes
    # home = str(Path.home()) + '/'
    # cache_dir = home + CONFIG_DIR
    # if not os.path.exists(cache_dir):
    #     os.mkdir(cache_dir, 0o755)
    # if not os.path.exists(cache_dir + CACHE_FILE):
    #     f = open(cache_dir + CACHE_FILE, "w+")
    #     f.write("# kxfed cache file. Created" + str(datetime.datetime.now()) + '\n')
    #     f.close()
    # f = open(cache_dir + CACHE_FILE, "r+")
    # KFConf.cache = Config(f)
    # unable to get config to play with make_region.configure_from_config
    # dot notation does not work
    # __this__.cache = make_region()
    # __this__.cache.configure_from_config(__this__.cfg, "cache.")
    __this__.cache = make_region().configure(
        backend=__this__.cfg['cache']['backend'],
        expiration_time=int(__this__.cfg['cache']['expiration_time']),
        arguments={
            'filename': __this__.cfg['cache']['arguments']['filename']
        }
    )
