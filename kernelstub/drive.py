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

import os
import logging

class NoBlockDevError(Exception):
    """No Block Device Found Exception"""

class UUIDNotFoundError(Exception):
    """No UUID for device found Exception"""

class Drive():
    """
    Kernelstub Drive Object

    Stores and retrieves information related to the current drive.
    """

    drive_name = 'none'
    root_fs = '/'
    root_path = '/'
    root_uuid = '12345-12345-12345'
    esp_fs = '/boot/efi'
    esp_path = '/boot/efi'
    esp_num = 0

    def __init__(self, root_path="/", esp_path="/boot/efi"):
        self.log = logging.getLogger('kernelstub.Drive')
        self.log.debug('loaded kernelstub.Drive')

        self.esp_path = esp_path
        self.root_path = root_path
        self.log.debug('root path = %s', self.root_path)
        self.log.debug('esp_path = %s', self.esp_path)

        self.mtab = self.get_drives()

        try:
            self.root_fs = self.get_part_dev(self.root_path)
            self.esp_fs = self.get_part_dev(self.esp_path)
            self.drive_name = self.get_drive_dev(self.esp_fs)
            self.esp_num = self.esp_fs[-1]
            self.root_uuid = self.get_uuid(self.root_fs[5:])
        except NoBlockDevError as e_e:
            self.log.exception(
                'Could not find a block device for the a partition. This is a'
                'critical error and we cannot continue.'
            )
            self.log.debug(e_e)
            exit(174)
        except UUIDNotFoundError as e_e:
            self.log.exception(
                'Could not find a block device for the a partition. This is a '
                'critical error and we cannot continue.'
            )
            self.log.debug(e_e)
            exit(177)


        self.log.debug('Root is on /dev/%s', self.drive_name)
        self.log.debug('root_fs = %s ', self.root_fs)
        self.log.debug('root_uuid is %s', self.root_uuid)


    def get_drives(self):
        """Returns a list of information about mounted filesystems."""
        self.log.debug('Getting a list of drives')
        with open('/proc/mounts', mode='r') as proc_mounts:
            mtab = proc_mounts.readlines()

        self.log.debug(mtab)
        return mtab

    def get_part_dev(self, path):
        """Returns a block device file for `path`."""
        self.log.debug('Getting the block device file for %s', path)
        for mount in self.mtab:
            drive = mount.split(" ")
            if drive[1] == path:
                part_dev = os.path.realpath(drive[0])
                self.log.debug('%s is on %s', path, part_dev)
                return part_dev
        raise NoBlockDevError(
            'Couldn\'t find the block device for {}'.format(path)
        )

    def get_drive_dev(self, blockdev):
        """Returns a block device for the drive partition blockdev is on."""
        # Ported from bash, out of @jackpot51's firmware updater
        efi_name = os.path.basename(blockdev)
        efi_sys = os.readlink('/sys/class/block/{}'.format(efi_name))
        disk_sys = os.path.dirname(efi_sys)
        disk_name = os.path.basename(disk_sys)
        self.log.debug('ESP is a partition on /dev/%s', disk_name)
        return disk_name

    def get_uuid(self, filesystem):
        """Get a UUID for a filesystem."""
        all_uuids = os.listdir('/dev/disk/by-uuid')
        self.log.debug('Looking for UUID for %s', filesystem)
        self.log.debug('List of UUIDs:\n%s', all_uuids)

        for uuid in all_uuids:
            uuid_path = os.path.join('/dev/disk/by-uuid', uuid)
            if filesystem in os.path.realpath(uuid_path):
                return uuid

        raise UUIDNotFoundError
