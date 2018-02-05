#!/usr/bin/python3

"""
 kernelstub
 The automatic manager for using the Linux Kernel EFI Stub to boot

 Copyright 2017-2018 Ian Santopietro <isantop@gmail.com>

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

Please see the provided LICENSE.txt file for additional distribution/copyright
terms.
"""

import os, subprocess, logging

class Drive():

    root_fs = '/'
    root_uuid = '12345-12345-12345'
    esp_fs = '/boot/efi'
    esp_path = '/boot/efi'
    esp_num = 0

    def __init__(self, root_path="/", esp_path="/boot/efi"):
        self.log = logging.getLogger('kernelstub.Drive')
        self.log.debug('Logging set up')
        self.log.debug('loaded kernelstub.Drive')

        self.esp_path = esp_path
        self.log.debug('esp_path = %s' % self.esp_path)

        self.drive_dict = self.parse_proc_partitions()
        self.log.debug('drive_dict = %s' % self.drive_dict)

        self.log.debug('root_path = %s' % root_path)
        self.root_fs = self.get_part_name(root_path)
        self.log.debug('root_fs = %s ' % self.root_fs)

        self.root_uuid = self.get_uuid(self.root_fs)
        self.esp_fs = self.get_part_name(esp_path)
        self.esp_num = self.esp_fs[-1]


    def get_part_name(self, path):
        major = self.get_maj(path)
        minor = self.get_min(path)
        name = self.drive_dict[(major, minor)]
        return name

    def parse_proc_partitions(self):
        res = {}
        with open('/proc/partitions', mode='r') as parts:
            for line in parts:
                fields = line.split()
                try:
                    tmaj = int(fields[0])
                    tmin = int(fields[1])
                    name = fields[3]
                    res[(tmaj, tmin)] = name
                except:
                    # just ignore parse errors in header/separator lines
                    pass
        return res

    def get_maj(self, path):
        dev = os.stat(path).st_dev
        major = os.major(dev)

        self.log.debug('Major for %s = %s' % (path, major))
        return major

    def get_min(self, path):
        dev = os.stat(path).st_dev
        minor = os.minor(dev)

        self.log.debug('Minor for %s = %s' % (path, minor))
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
    
