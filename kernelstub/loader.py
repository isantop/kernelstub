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
"""

import os

class Loader():

    loader_dir = '/boot/efi/loader'
    entry_dir = '/boot/efi/loader/entries'

    def __init__(self, log):
        self.log = log
        if not os.path.exists(self.loader_dir):
            os.makedirs(self.loader_dir)
        if not os.path.exists(self.entry_dir):
            os.makedirs(self.entry_dir)

    def write_config(self, os_name, os_version, kopts, overwrite=False):
        title_line = 'title %s %s' %(os_name, os_version)
        linux_line = 'linux /EFI/%s-kernelstub/vmlinuz-current' % os_name
        initrd_line = 'initrd /EFI/%s-kernelstub/initrd-current' % os_name
        option_line = 'options %s' % kopts
        with open('%s/%s-current.conf' % (self.entry_dir, os_name), mode='w') as entry:
            entry.write('%s\n' % title_line)
            entry.write('%s\n' % linux_line)
            entry.write('%s\n' % initrd_line)
            entry.write('%s\n' % option_line)

        if not overwrite:
            if not os.path.exists('%s/loader.conf' % self.loader_dir):
                overwrite = True

        if overwrite:
            entry_name = '%s-current' % os_name
            with open('%s/loader.conf' % self.loader_dir, mode='w') as loader:
                default_line = 'default %s\n' % entry_name
                loader.write(default_line)
