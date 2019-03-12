#!/usr/bin/python3

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib


class PkgException(dbus.DBusException):
    _dbus_error_name = "uk.co.jerlesey.kxfed.PkgException"


class InstallPkgs(dbus.service.Object):
    def __init__(self, bus_name):
        try:
            super().__init__(bus_name, "/InstallPkgs")
        except dbus.DBusException:
            raise PkgException("Exception in install pkgs")

    @dbus.service.signal("uk.co.jerlesey.kxfed.InstallPkgs", signature='s')
    def progress_label(self, converted):
        # The signal is emitted when this method exits
        # You can have code here if you wish
        pass


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    mainloop = GLib.MainLoop()
    dbus.mainloop.glib.threads_init()

    try:
        session_bus = dbus.SessionBus()
        session_bus_name = dbus.service.BusName("uk.co.jerlesey.kxfed.Signal", bus=session_bus, do_not_queue=True)
    except dbus.exceptions.NameExistsException:
        print("service is already running")
        sys.exit(1)
    except dbus.exceptions.DBusException as e:
        print(str(e))


    try:
        object = InstallPkgs(session_bus_name)
        mainloop.run()
    except KeyboardInterrupt:
        print("keyboard interrupt received")
    except Exception as e:
        print("unhandled exception occurred:")
    finally:
        mainloop.quit()

