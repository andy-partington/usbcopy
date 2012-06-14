#!/usr/bin/python

import dbus
import sys
import os
import datetime
from shutil import copy2
from shutil import copytree
from shutil import rmtree

# This is the only area you should change

sources = [ '/home/andy/Pictures', '/home/andy/Projects']

# End 
# TODO: Add to a config file so script never gets altered

def GetDiskInfo():
    #Probes dbus to find any attached/mounted/unmount USB drives and mounts if found and unmounted
    bus = dbus.SystemBus()
    ud_manager_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
    ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks')
    disks = {}
    for dev in ud_manager.EnumerateDevices():
        device_obj = bus.get_object("org.freedesktop.UDisks", dev)
        device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
        if not device_props.Get('org.freedesktop.UDisks.Device',"DeviceIsDrive"):
            if device_props.Get('org.freedesktop.UDisks.Device', "DriveConnectionInterface") == 'usb':
                if not device_props.Get('org.freedesktop.UDisks.Device', 'DeviceIsMounted'):
                    drivename = device_props.Get('org.freedesktop.UDisks.Device', 'DriveModel')
                    print "Drive %s not mounted - mounting" % (drivename)
                    device_obj.FilesystemMount('', [], dbus_interface='org.freedesktop.UDisks.Device')
                    
                devFile = str(device_props.Get('org.freedesktop.UDisks.Device',"DeviceFile"))
                devPath = str(device_props.Get('org.freedesktop.UDisks.Device',"DeviceMountPaths")[0])
                disks[devFile] = devPath
        
    return disks  
    
def backupops():    
    usb_disks = GetDiskInfo()
    if len(usb_disks) == 1 : #Check that only 1 USB device is attached and mounted else fail
        dest_mnt = usb_disks.values()[0]
        day = datetime.datetime.now()
        day = day.strftime("%a")
        dest = ''.join([dest_mnt, '/', day])
        
        if os.path.isdir(dest) == True :
            print "Deleting old dir %s" % (dest)
            rmtree(dest)

        for src in sources :
            extra_path = src.rsplit("/", 1)[1]
            full_dest = ''.join([dest, '/', extra_path])
            print "Copying from %s to %s" % (src, full_dest)
            copytree(src, full_dest)


        bus = dbus.SystemBus()
        ud_manager_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
        ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks') 
        dev = ud_manager.FindDeviceByDeviceFile(usb_disks.keys()[0]) 
        device_obj = bus.get_object("org.freedesktop.UDisks", dev) 
        device_obj.FilesystemUnmount([], dbus_interface='org.freedesktop.UDisks.Device')
        return 0
    else:  #If we don't have USB drives attached and mounted
        if len(usb_disks) > 1 :
            print "More than one USB drive detected, aborting"
        else:
            print "No USB drives were detected, aborting"
            
        return 1
        
if __name__ == '__main__':
    sys.exit(backupops())         

