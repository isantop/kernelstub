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

import subprocess

class NVRAM():

    os_entry_index = -1
    os_label = ""
    nvram = []
    order_num = "0000"

    def __init__(self, name, version):
        self.os_label = "%s %s" % (name, version)
        self.nvram = self.get_nvram()
        self.find_os_entry(self.nvram, self.os_label)
        self.order_num = str(self.nvram[self.os_entry_index])[4:8]

    def update(self):
        self.nvram = self.get_nvram()
        self.find_os_entry(self.nvram, self.os_label)
        self.order_num = str(self.nvram[self.os_entry_index])[4:8]

    def get_nvram(self):
        command = ['/usr/bin/sudo',
                   'efibootmgr']
        nvram = subprocess.check_output(command).decode('UTF-8').split('\n')
        return nvram



    def find_os_entry(self, nvram, os_label):
        self.os_entry_index = -1
        find_index = self.os_entry_index
        for entry in nvram:
            find_index = find_index + 1
            if os_label in entry:
                self.os_entry_index = find_index
                return find_index


    def add_entry(self, this_os, this_drive, kernel_opts):
        device = '/dev/%s' % this_drive.drive_name
        esp_num = this_drive.esp_num
        entry_label = '%s %s' % (this_os.os_name, this_os.os_version)
        entry_linux = '\\EFI\\%s\\vmlinuz' % this_os.os_name
        root_uuid = this_drive.root_uuid
        entry_initrd = 'EFI/%s/initrd' % this_os.os_name
        kernel_opts = kernel_opts
        command = ['/usr/bin/sudo',
                   'efibootmgr',
                   '-d', device,
                   '-p', esp_num,
                   '-c',
                   '-L', '"%s"' % entry_label,
                   '-l', entry_linux,
                   '-u',
                   '"root=UUID=%s' % root_uuid,
                   'initrd=%s' % entry_initrd,
                   'ro']
        for option in kernel_opts:
            command.append(option)
        command.append('"')
        subprocess.run(command)
        self.update()

    def delete_boot_entry(self, index):
        command = ['/usr/bin/sudo',
                   'efibootmgr',
                   '-B',
                   '-b', str(index)]
        subprocess.run(command)
        self.update()
