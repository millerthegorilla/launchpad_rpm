from package_process import PackageProcess
from multiprocessing.dummy import Pool as ThreadPool
from kfconf import pkg_states, cfg, \
                   rpms_dir, add_item_to_section, pkg_search
from os.path import isfile
from os import remove
import logging
from subprocess import Popen, PIPE
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QGuiApplication
from threading import RLock


class ConversionProcess(PackageProcess):
    def __init__(self, *args, log_signal=None, msg_signal=None, progress_signal=None, transaction_progress_signal=None):
        super(ConversionProcess, self).__init__(*args, msg_signal=msg_signal, log_signal=log_signal)
        self._section = "converting"
        self._error_section = "failed_converting"
        self._next_section = "installing"
        self._path_name = "rpm_path"
        self._thread_pool = ThreadPool(10)
        self._process = None
        self._progress_signal = progress_signal
        self._transaction_progress_signal = transaction_progress_signal
        self._lock = RLock()

    def state_change(self, callback=None):
        self._action_finished_callback = callback
        deb_paths_list = []
        for i in self:
            if isfile(i.pkg['deb_path']):
                deb_paths_list.append(str(i.pkg['deb_path']))
            else:
                add_item_to_section('failed_download', i.pkg.parent.pop(i.pkg))

        if cfg['convert'] == 'True' and cfg['distro_type'] == 'rpm':
            self._log_signal.emit('Converting packages : ' + str(deb_paths_list), logging.INFO)
            self._msg_signal.emit('Converting Packages...')

            self._thread_pool.apply_async(self._convert_packages,
                                          (deb_paths_list,),
                                          callback=self._conversion_finished)

    def _conversion_finished(self, tup):
        num_conv, deb_path_length = tup
        if num_conv == deb_path_length:
            self._msg_signal.emit("All packages successfully converted.")
            self._log_signal.emit("All packages successfully converted.", logging.INFO)
            self._action_finished_callback(num_conv, deb_path_length)
        else:
            self._msg_signal.emit(str(deb_path_length - num_conv) + " Some packages were not converted.")
            self._log_signal.emit(str(deb_path_length - num_conv) + " packages were not converted.", logging.INFO)
            self._action_finished_callback(deb_path_length - num_conv, deb_path_length)

    def _convert_packages(self, deb_path_list):
        deb_length = len(deb_path_list)
        from getpass import getuser
        username = getuser()
        del getuser
        try:
            self._process = Popen(['pkexec', '/home/james/Src/kxfed/build_rpms.sh', username,
                                  cfg['rpms_dir'], cfg['arch']] + deb_path_list,
                                  bufsize=1,
                                  stdin=PIPE,
                                  stdout=PIPE,
                                  stderr=PIPE)
        except Exception as e:
            self._log_signal.emit(e)
        num_of_conv = 0
        i = 0
        while 1:
            QGuiApplication.instance().sendPostedEvents()
            QApplication.instance().processEvents()
            QGuiApplication.instance().processEvents()
            next_line = self._process.stdout.readline().decode('utf-8')
            self._process.stdout.flush()
            i += 1
            self._lock.acquire()
            self._progress_signal.emit(i % 17, deb_length * 17)
            self._log_signal.emit(next_line, logging.INFO)
            self._lock.release()
            if 'Converted' in next_line:
                word_list = next_line.split(' to ')
                rpm_name = word_list[1].rstrip('\n')
                deb_path = word_list[0].lstrip('Converted ')
                found_pkg = pkg_search([self._section], search_value=deb_path)
                if found_pkg:
                    if isfile(rpms_dir + rpm_name):
                        pkg_states[self._section][found_pkg.parent.name][found_pkg.name]['rpm_path'] = \
                            rpms_dir + rpm_name
                    num_of_conv += 1
                    if isfile(found_pkg['deb_path']) and cfg['delete_downloaded'] == 'True':
                        remove(found_pkg['deb_path'])
                        found_pkg['deb_path'] = ""
                    self._lock.acquire()
                    self._transaction_progress_signal.emit(num_of_conv, deb_length)
                    self._msg_signal.emit(next_line)
                    self._lock.release()
            if next_line == '' and self._process.poll() is not None:
                self._progress_signal.emit(0, 0)
                self._transaction_progress_signal.emit(0, 0)
                break
        if num_of_conv > 0:
            for ppa in pkg_states[self._section]:
                if pkg_states[self._section][ppa]:
                    for pkg_id in pkg_states[self._section][ppa]:
                        if not isfile(pkg_states[self._section][ppa][pkg_id][self._path_name]):
                            self._lock.acquire()
                            self._log_signal.emit('Error - did not convert ' +
                                                  pkg_states[self._section][ppa][pkg_id]['name'], logging.INFO)
                            self._lock.release()
        else:
            self._log_signal.emit(Exception("There is an error with the bash script when converting."), logging.CRITICAL)
            return False
        self._lock.acquire()
        self._msg_signal.emit("Converted " + str(num_of_conv) + " out of " + str(deb_length))
        self._log_signal.emit("Converted " + str(num_of_conv) + " out of " + str(deb_length), logging.INFO)
        self._progress_signal.emit(0, 0)
        self._transaction_progress_signal.emit(0, 0)
        self._lock.release()
        return num_of_conv, deb_length
