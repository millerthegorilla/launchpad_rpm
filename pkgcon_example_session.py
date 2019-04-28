import dbus
import sys

try:
    bus = dbus.SystemBus()
except dbus.DBusException as e:
    print('Unable to connect to dbus: %s' % str(e))
    sys.exit()
try:
    proxy = bus.get_object('org.freedesktop.PackageKit', '/org/freedesktop/PackageKit')
    iface = dbus.Interface(proxy, 'org.freedesktop.PackageKit.Modify2')
    proxy.createTransaction()
    # iface.InstallPackageNames(dbus.UInt32(0), ["openoffice-clipart", "openoffice-clipart-extras"], "show-confirm-search,hide-finished")
except dbus.DBusException as e:
    print('Unable to use PackageKit: %s' % str(e))
