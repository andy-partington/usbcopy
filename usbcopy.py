#!/usr/bin/python

import dbus
import sys
import os
import datetime
from shutil import copy2
from shutil import copytree
from shutil import rmtree

# This is the only area you should change

sources = [ '/home/andy/Pictu', '/home/andy/Projects']

# End 
# TODO: Add to a config file so script never gets altered

def freespace(p):
	s = os.statvfs(p)
	return (s.f_bsize * s.f_bavail)

def totalspace(p):
	s = os.statvfs(p)
	return (s.f_bsize * s.f_blocks)

def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fT' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size
    
def reportspace(direc):
    free = convert_bytes(freespace(direc))
    total = convert_bytes(totalspace(direc))

    print "Space available %s of %s" % (free, total)
    
def du_sk(start_path = '.'):
    total_size = 0
  
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.stat(fp).st_size
 	  
    return total_size    

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
            
            if os.path.isdir(src):
                print "Copying %s from %s to %s" % (convert_bytes(du_sk(src)), src, full_dest)
                copytree(src, full_dest)
                print "Backed up %s to %s" % (convert_bytes(du_sk(full_dest)), full_dest)
            else:
                print "Can't find %s directory, skipping..." % (src)
            

        bus = dbus.SystemBus()
        ud_manager_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
        ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks') 
        dev = ud_manager.FindDeviceByDeviceFile(usb_disks.keys()[0]) 
        device_obj = bus.get_object("org.freedesktop.UDisks", dev) 
        reportspace(usb_disks.values()[0])
        
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

