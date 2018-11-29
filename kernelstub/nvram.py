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

import logging
import subprocess

class NVRAM():
    """
    Kernelstub NVRAM object.

    Provides methods for interacting with the system NVRAM variables.
    """
    os_entry_index = -1
    os_label = ""
    nvram = []
    order_num = "0000"

    def __init__(self, name, version):
        self.log = logging.getLogger('kernelstub.NVRAM')
        self.log.debug('loaded kernelstub.NVRAM')

        self.os_label = "{} {}".format(name, version)
        self.update()

    def update(self):
        """Make sure we're looking at the correct NVRAM entry."""
        self.log.debug('Updating NVRAM info')
        self.nvram = self.get_nvram()
        self.find_os_entry(self.nvram, self.os_label)
        if self.os_entry_index >= 0:
            self.order_num = str(self.nvram[self.os_entry_index])[4:8]

    def get_nvram(self):
        """Retrieve NVRAM data from system."""
        self.log.debug('Getting NVRAM data')
        command = [
            '/usr/bin/sudo',
            'efibootmgr'
        ]
        try:
            return subprocess.check_output(command).decode('UTF-8').split('\n')
        except Exception as e_e:
            self.log.exception('Failed to retrieve NVRAM data. Are you running in a chroot?')
            self.log.debug(e_e)
            return []

    def find_os_entry(self, nvram, os_label):
        """Find an NVRAM entry for the current OS."""
        self.log.debug('Finding NVRAM entry for %s', os_label)
        self.os_entry_index = -1
        find_index = self.os_entry_index
        for entry in nvram:
            find_index += 1
            if os_label in entry:
                self.os_entry_index = find_index
                self.log.debug('Entry found! Index: %s', self.os_entry_index)
                return find_index


    def add_entry(self, this_os, this_drive, kernel_opts, simulate=False):
        """Add an entry into the NVRAM."""
        self.log.info('Creating NVRAM entry')
        device = '/dev/{}'.format(this_drive.drive_name)
        esp_num = this_drive.esp_num
        entry_label = '{} {}'.format(this_os.name, this_os.version)
        entry_linux = '\\EFI\\{}-{}\\vmlinuz.efi'.format(this_os.name, this_drive.root_uuid)
        entry_initrd = 'EFI/{}-{}/initrd.img'.format(this_os.name, this_drive.root_uuid)
        command = [
            '/usr/bin/sudo',
            'efibootmgr',
            '-c',
            '-d', device,
            '-p', esp_num,
            '-L', '{}'.format(entry_label),
            '-l', '{}'.format(entry_linux),
            '-u',
            'initrd={} {}'.format(entry_initrd, kernel_opts)
        ]
        self.log.debug('NVRAM command:\n%s', command)
        if not simulate:
            try:
                subprocess.run(command)
            except subprocess.SubprocessError as e_e:
                self.log.exception(
                    'Couldn\'t create boot entry for kernel! This means that '
                    'the system will not boot from the new kernel directly. Do '
                    'NOT reboot without an alternate bootloader configured or '
                    'fixing this problem. More information is available in the '
                    'log or by running again with -vv'
                )
                self.log.debug(e_e)
                exit(172)
        self.update()

    def delete_boot_entry(self, index, simulate):
        """Delete an entry from the NVRAM."""
        self.log.info('Deleting old boot entry: %s', index)
        command = ['/usr/bin/sudo',
                   'efibootmgr',
                   '-B',
                   '-b', str(index)]
        self.log.debug('NVRAM command:\n%s', command)
        if not simulate:
            try:
                subprocess.run(command)
            except Exception as e_e:
                self.log.exception(
                    'Couldn\'t delete old boot entry %s. This could cause '
                    'problems, so kernelstub will not continue. Check again '
                    'with -vv for more info.', index
                )
                self.log.debug(e_e)
                exit(173)
        self.update()
