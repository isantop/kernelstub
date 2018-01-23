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

import os

class OS():

    os_name = "Linux"
    os_version = "1.0"
    os_cmdline = ['quiet', 'splash']

    def __init__(self):
        self.os_name = self.get_os_name()
        self.os_version = self.get_os_version()
        self.os_cmdline = self.get_os_cmdline()

    def get_os_cmdline(self):
        with open('/proc/cmdline') as cmdline_file:
            cmdline_list = cmdline_file.readlines()[0].split(" ")

        cmdline = []
        for option in cmdline_list:
            if not option.startswith('BOOT_IMAGE'):
                if not option.startswith('root='):
                    if not option.startswith('initrd='):
                        cmdline.append(option)
        return cmdline

        return cmdline_string

    def get_os_name(self):
        os_release = self.get_os_release()
        for item in os_release:
            if item.startswith('NAME='):
                name = item.split('=')[1]
                return self.strip_quotes(name[:-1])

    def get_os_version(self):
        os_release = self.get_os_release()
        for item in os_release:
            if item.startswith('VERSION_ID='):
                version =  item.split('=')[1]
                return self.strip_quotes(version[:-1])

    def strip_quotes(self, value):
        new_value = value
        if value.startswith('"'):
            new_value = new_value[1:]
        if value.endswith('"'):
            new_value = new_value[:-1]
        return new_value

    def get_os_release(self):
        try:
            with open('/etc/os-release') as os_release_file:
                os_release = os_release_file.readlines()
        except FileNotFoundError:
            os_release = ['NAME="%s"\n' % self.os_name,
                          'VERSION="%s"\n' % self.os_version,
                          'ID=linux\n',
                          'ID_LIKE=linux\n',
                          'VERSION_ID="%s"\n' % self.os_version]

        return os_release
