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

import platform

class OS():

    name_pretty = "Linux"
    name = "Linux"
    version = "1.0"
    cmdline = ['quiet', 'splash']
    kernel_name = 'vmlinuz'
    initrd_name = 'initrd.img'
    old_kernel_name = 'vmlinuz.old'
    old_initrd_name = 'initrd.img.old'
    kernel_release = platform.release()
    kernel_path = '/vmlinuz'
    initrd_path = '/initrd.img'
    old_kernel_path = '/vmlinuz.old'
    old_initrd_path = '/initrd.img.old'

    def __init__(self):
        self.name_pretty = self.get_os_name()
        self.name = self.clean_names(self.name_pretty)
        self.version = self.get_os_version()
        self.cmdline = self.get_os_cmdline()

    def clean_names(self, name):
        # This is a list of characters we can't/don't want to have in technical
        # names for the OS. name_pretty will still have them.
        badchar = {
            ' ' : '_',
            '~' : '-',
            '!' : '',
            "'" : "",
            '<' : '',
            '>' : '',
            ':' : '',
            '"' : '',
            '/' : '',
            '\\' : '',
            '|' : '',
            '?' : '',
            '*' : '',
            'CON' : '',
            'PRN' : '',
            'AUX' : '',
            'NUL' : '',
            'COM1' : '',
            'COM2' : '',
            'COM3' : '',
            'COM4' : '',
            'COM5' : '',
            'COM6' : '',
            'COM7' : '',
            'COM8' : '',
            'COM9' : '',
            'LPT1' : '',
            'LPT2' : '',
            'LPT3' : '',
            'LPT4' : '',
            'LPT5' : '',
            'LPT6' : '',
            'LPT7' : '',
            'LPT8' : '',
            'LPT9' : '',
        }

        for char in badchar:
            name = name.replace(char, badchar[char])
        return name

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
            os_release = ['NAME="%s"\n' % self.name,
                          'ID=linux\n',
                          'ID_LIKE=linux\n',
                          'VERSION_ID="%s"\n' % self.version]

        return os_release
