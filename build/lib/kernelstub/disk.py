#!/usr/bin/python3

"""
 kernelstub Version 0.2

 The automatic manager for using the Linux Kernel EFI Stub to boot

 Copyright 2017 Ian Santopietro <isantop@gmail.com>

Permission to use, copy, modify, and/or distribute this software for any purpose
with or without fee is hereby granted, provided that the above copyright notice
and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.

 This program will automatically keep a copy of the Linux Kernel image and your
 initrd.img located on your EFI System Partition (ESP) on an EFI-compatible
 system. The benefits of this approach include being able to boot Linux directly
 and bypass the GRUB bootloader in many cases, which can save 4-6 seconds during
 boot on a system with a fast drive. Please note that there are no guarantees
 about boot time saved using this method.

 For maximum safety, kernelstub recommends leaving an entry for GRUB in your
 system's ESP and NVRAM configuration, as GRUB allows you to modify boot
 parameters per-boot, which loading the kernel directly cannot do. The only
 other way to do this is to use an EFI shell to manually load the kernel and
 give it parameters from the EFI Shell. You can do this by using:

 fs0:> vmlinuz-image initrd=EFI/path/to/initrd/stored/on/esp options

 kernelstub will load parameters from the /etc/default/kernelstub config file.
"""

import os, subprocess

class Disk():

    drive_name = "none"
    root_fs = "/"
    root_uuid = "12345-12345-12345"
    esp_fs = "/boot/efi"
    esp_num = 0

    def __init__(self, root_path="/", esp_path="/boot/efi"):
        self.drive_name = self.get_drive_name(root_path)
        self.root_fs = self.get_part_name(root_path)
        self.root_uuid = self.get_uuid(self.root_fs)
        self.esp_fs = self.get_part_name(esp_path)
        self.esp_num = self.esp_fs[-1]

    def get_drive_name(self, path):
        major = self.get_maj(path)
        dInfo = self.parse_proc_partitions()
        name = dInfo[(major, 0)]
        return name

    def get_part_name(self, path):
        major = self.get_maj(path)
        minor = self.get_min(path)
        pInfo = self.parse_proc_partitions()
        name = pInfo[(major, minor)]
        return name

    def parse_proc_partitions(self):
        res = {}
        f = open("/proc/partitions", "r")
        for line in f:
            fields = line.split()
            try:
                tmaj = int(fields[0])
                tmin = int(fields[1])
                name = fields[3]
                res[(tmaj, tmin)] = name
            except:
                # just ignore parse errors in header/separator lines
                pass
        f.close()
        return res

    def get_maj(self, path):
        dev = os.stat(path).st_dev
        major = os.major(dev)
        return major

    def get_min(self, path):
        dev = os.stat(path).st_dev
        minor = os.minor(dev)
        return minor

    def get_uuid(self, fs):
        disks_bytes = subprocess.check_output(['/bin/ls',
                                               '-la',
                                               '/dev/disk/by-uuid'])
        disks_info = disks_bytes.decode('UTF-8')
        disks_list = disks_info.split("\n")

        for disk in disks_list:
            info_list = disk.split(" ")
            if info_list[-1].endswith(fs):
                return info_list[-3]
    
