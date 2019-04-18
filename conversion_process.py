from package_process import PackageProcess
from multiprocessing.dummy import Pool as ThreadPool
from kfconf import pkg_states, cfg, add_item_to_section, delete_ppa_if_empty
from os.path import isfile, basename, exists
from os import remove
import logging
from subprocess import Popen, PIPE
from PyQt5.QtGui import QGuiApplication


class ConversionProcess(PackageProcess, list):
    def __init__(self, *args, lock_model_signal=None, log_signal=None, msg_signal=None, progress_signal=None):
        super(ConversionProcess, self).__init__(args)
        self._section = "converting"
        self._thread_pool = ThreadPool(10)
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self._progress_signal = progress_signal

    def state_change(self):
        deb_paths_list = []
        for i in self:
            if isfile(i.pkg['deb_path']):
                deb_paths_list.append(i.pkg['deb_path'])

        if cfg['convert'] == 'True' and cfg['distro_type'] == 'rpm':
            self._log_signal.emit('Converting packages : ' + str(deb_paths_list), logging.INFO)
            self._msg_signal.emit('Converting Packages...')

            result = self._thread_pool.apply_async(self._convert_packages,
                                                   (deb_paths_list,),
                                                   callback=self.conversion_finished_signal.emit)

    def _convert_packages(self, deb_path_list):
        from getpass import getuser
        username = getuser()
        del getuser
        try:
            self.process = Popen(['pkexec', '/home/james/Src/kxfed/build_rpms.sh', username,
                                  cfg['rpms_dir'], cfg['arch']] + deb_path_list,
                                 bufsize=1,
                                 stdin=PIPE,
                                 stdout=PIPE,
                                 stderr=PIPE)
        except Exception as e:
            self.log_signal.emit(e)
        conv = False
        num_of_conv = 0
        while 1:
            if self.cancel_process:
                return False
            QGuiApplication.instance().processEvents()
            nextline = self.process.stdout.readline().decode('utf-8')
            self.process.stdout.flush()
            self.log_signal.emit(nextline, logging.INFO)
            if 'Converted' in nextline:
                word_list = nextline.split(' to ')
                rpm_name = word_list[1].rstrip('\n')
                deb_path = word_list[0].lstrip('Converted ')
                found_pkg = self.pkg_search(['converting'], search_value=deb_path)
                if found_pkg:
                    if not pkg_states['installing']:
                        pkg_states['installing'] = {}
                    if found_pkg.parent.name not in pkg_states['installing']:
                        pkg_states['installing'][found_pkg.parent.name] = {}
                    pkg_states['installing'][found_pkg.parent.name][found_pkg.name] = \
                        pkg_states['converting'][found_pkg.parent.name].pop(found_pkg.name)
                    pkg_states['installing'][found_pkg.parent.name][found_pkg.name]['rpm_path'] = \
                        cfg['rpms_dir'] + rpm_name
                    conv = True
                    num_of_conv += 1
                    if exists(found_pkg['deb_path']) and cfg['delete_downloaded'] == 'True':
                        remove(found_pkg['deb_path'])
                    self._progress_signal.emit(num_of_conv, len(deb_path_list))
                    self._msg_signal.emit(nextline)
                else:
                    conv = False
            if nextline == '' and self.process.poll() is not None:
                break
        if conv is True:
            cfg.filename = (cfg['config']['dir'] + cfg['config']['filename'])
            cfg.write()
            for ppa in pkg_states['converting']:
                if pkg_states['converting'][ppa]:
                    for pkg in pkg_states['converting'][ppa]:
                        self._log_signal.emit('Error - did not convert ' + str(pkg.name), logging.INFO)
            pkg_states['converting'] = {}
        else:
            self._log_signal.emit(Exception("There is an error with the bash script when converting."), logging.CRITICAL)
            return False
        return True
