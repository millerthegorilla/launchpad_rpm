from package_process import PackageProcess
from multiprocessing.dummy import Pool as ThreadPool
from kfconf import pkg_states, cfg, rpms_dir, add_item_to_section
from os.path import isfile
from os import remove
import logging
from subprocess import Popen, PIPE
from PyQt5.QtGui import QGuiApplication


class ConversionProcess(PackageProcess, list):
    def __init__(self, *args, log_signal=None, msg_signal=None, progress_signal=None):
        super(ConversionProcess, self).__init__(args)
        self._section = "converting"
        self._error_section = "failed_conversion"
        self._next_section = "installing"
        self._path_name = "rpm_path"
        self._thread_pool = ThreadPool(10)
        self._msg_signal = msg_signal
        self._log_signal = log_signal
        self._progress_signal = progress_signal

    def state_change(self):
        deb_paths_list = []
        for i in self:
            if isfile(i.pkg['deb_path']):
                deb_paths_list.append(i.pkg['deb_path'])
            else:
                add_item_to_section('failed_download', i.pkg.parent.pop(i.pkg))

        if cfg['convert'] == 'True' and cfg['distro_type'] == 'rpm':
            self._log_signal.emit('Converting packages : ' + str(deb_paths_list), logging.INFO)
            self._msg_signal.emit('Converting Packages...')

            result = self._thread_pool.apply_async(self._convert_packages,
                                                   (deb_paths_list,))
            if result.get() is not False:
                if result.get() == len(deb_paths_list):
                    self._msg_signal("All packages successfully converted.")
                    self._log_signal("All packages successfully converted.", logging.INFO)
                    return 0, result.get()
                else:
                    self._msg_signal("Some packages were not converted.")
                    self._log_signal("Some packages were not converted.", logging.INFO)
                    return -1, result.get()
            else:
                return -1, len(deb_paths_list) - result.get()

    def _convert_packages(self, deb_path_list):
        deb_length = len(deb_path_list)
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
            self._log_signal.emit(e)
        num_of_conv = 0
        while 1:
            QGuiApplication.instance().processEvents()
            nextline = self.process.stdout.readline().decode('utf-8')
            self.process.stdout.flush()
            self.log_signal.emit(nextline, logging.INFO)
            if 'Converted' in nextline:
                word_list = nextline.split(' to ')
                rpm_name = word_list[1].rstrip('\n')
                deb_path = word_list[0].lstrip('Converted ')
                found_pkg = self.pkg_search([self._section], search_value=deb_path)
                if found_pkg:
                    if isfile(rpms_dir + rpm_name):
                        pkg_states[self._section][found_pkg.parent.name][found_pkg.name]['rpm_path'] = \
                            rpms_dir + rpm_name
                    num_of_conv += 1
                    if isfile(found_pkg['deb_path']) and cfg['delete_downloaded'] == 'True':
                        remove(found_pkg['deb_path'])
                        found_pkg['deb_path'] = ""
                    self._progress_signal.emit(num_of_conv, deb_length)
                    self._msg_signal.emit(nextline)
            if nextline == '' and self.process.poll() is not None:
                break
        if num_of_conv > 0:
            for ppa in pkg_states[self._section]:
                if pkg_states[self._section][ppa]:
                    for pkg_id in pkg_states[self._section][ppa]:
                        if not isfile(pkg_states[self._section][ppa][pkg_id][self._path_name]):
                            self._log_signal.emit('Error - did not convert ' +
                                                  pkg_states[self._section][ppa][pkg_id]['name'], logging.INFO)
        else:
            self._log_signal.emit(Exception("There is an error with the bash script when converting."), logging.CRITICAL)
            return False
        self._msg_signal.emit("Converted " + num_of_conv + " out of " + str(deb_length))
        self._log_signal.emit("Converted " + num_of_conv + " out of " + str(deb_length), logging.INFO)
        return num_of_conv
