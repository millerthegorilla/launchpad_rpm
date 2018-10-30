# config.py
import sys, os
from pathlib import Path
import datetime
from config import Config
from dogpile.cache import make_region
CONFIG_DIR = '.config/kxfed/'
CONFIG_FILE = 'kxfed.conf'


class KFConf:

    cfg = None
    cache = None

    def __init__(self):
        # launchpadlib config - not necessary or move to module level / outer scope
        home = str(Path.home()) + '/'
        lp_cache_dir = home + ".launchpadlib/api.launchpad.net/cache/"
        if not os.path.exists(lp_cache_dir):
            os.mkdir(lp_cache_dir, 0o755)

        if KFConf.cfg is None:
            # also in local function scope. no scope specifier like global is needed
            config_dir = home + CONFIG_DIR
            if not os.path.exists(config_dir):
                os.mkdir(config_dir, 0o755)
            if not os.path.exists(config_dir + CONFIG_FILE):
                f = open(config_dir + CONFIG_FILE, "w+")
                f.write("# kxfed configuration file. Created " + str(datetime.datetime.now()) + "\n")
                f.write("# constants\nCONFIG_DIR : '" + CONFIG_DIR + "'\nCONFIG_FILE : '" + CONFIG_FILE + "'\n")
                f.close()
            f = open(config_dir + CONFIG_FILE, "r+")
            KFConf.cfg = Config(f)
            KFConf.cfg.config_dir = config_dir

        if KFConf.cache is None:
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
            KFConf.cache = make_region().configure(
                backend=KFConf.cfg.cache.local.backend,
                expiration_time=KFConf.cfg.cache.local.expiration_time,
                arguments={
                    'filename': KFConf.cfg.config_dir + KFConf.cfg.cache.local.arguments.filename
                }
            )

KFConf()