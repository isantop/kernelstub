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

Please see the provided LICENCE.txt file for additional distribution/copyright
terms.
"""

import os, shutil, logging

class FileOpsError(Exception):
    pass

class Installer():

    loader_dir = '/boot/efi/loader'
    entry_dir = '/boot/efi/loader/entries'
    os_dir_name = 'linux-kernelstub'
    work_dir = '/boot/efi/EFI/'

    def __init__(self, nvram, opsys, drive):
        self.log = logging.getLogger('kernelstub.Installer')
        self.log.debug('Logging set up')
        self.log.debug('loaded kernelstub.Installer')

        self.nvram = nvram
        self.opsys = opsys
        self.drive = drive

        self.os_dir_name = "%s-%s" % (self.opsys.name, self.drive.root_uuid)
        self.kernel_dest = '%s%s/%s' % (self.work_dir, self.os_dir_name,
                                        self.opsys.kernel_name)
        self.initrd_dest = '%s%s/%s' % (self.work_dir, self.os_dir_name,
                                        self.opsys.initrd_name)

        if not os.path.exists(self.loader_dir):
            os.makedirs(self.loader_dir)
        if not os.path.exists(self.entry_dir):
            os.makedirs(self.entry_dir)

    def backup_old(self, simulate=False):
        self.log.info('Backing up old kernel')
        try:
            self.copy_files(
                '%s-current.efi' % self.kernel_dest,
                '%s-previous.efi' % self.kernel_dest,
                simulate=simulate
            )
        except:
            pass
        try:
            self.copy_files(
                '%s-current' % self.initrd_dest,
                '%s-previous' % self.initrd_dest,
                simulate=simulate
            )
        except:
            pass

    def setup_kernel(self, simulate=False):
        self.log.info('Copying Kernel into ESP')
        kernel_src = '/boot/%s-%s' % (self.opsys.kernel_name,
                                      self.opsys.kernel_release)
        initrd_src = '/boot/%s-%s' % (self.opsys.initrd_name,
                                      self.opsys.kernel_release)
        kernel_dest = '%s-current.efi' % self.kernel_dest
        initrd_dest = '%s-current'     % self.initrd_dest

        self.log.debug('Copying kernel:\n  %s => %s' % (kernel_src, kernel_dest))
        try:
            self.copy_files(
                kernel_src,
                kernel_dest,
                simulate=simulate
            )
        except FileOpsError:
            self.log.critical('Couldn\'t copy the kernel onto the ESP!\n' +
                              'This is a critical error and we cannot continue. Check your settings to see if ' +
                              'there is a typo. Otherwise, check permissions and try again.')
            exit(3)


        self.log.debug('Copying initrd:\n  %s => %s' % (initrd_src, initrd_dest))
        try:
            self.copy_files(
                initrd_src,
                initrd_dest,
                simulate=simulate
            )
        except FileOpsError:
            self.log.critical('Couldn\'t copy the initrd onto the ESP!\n' +
                              'This is a critical error and we cannot continue. Check your settings to see if ' +
                              'there is a typo. Otherwise, check permissions and try again.')
            exit(3)
        self.log.info('Copy complete')

    def setup_stub(self, kernel_opts, simulate=False):
        self.log.info("Setting up Kernel EFISTUB loader...")
        self.copy_cmdline(simulate=simulate)
        self.nvram.update()
        if self.nvram.os_entry_index >= 0:
            self.log.info("Deleting old boot entry")
            self.nvram.delete_boot_entry(self.nvram.order_num)
        else:
            self.log.debug("No old entry found, skipping removal.")
        self.nvram.add_entry(self.opsys, self.drive, kernel_opts)
        self.nvram.update()
        self.log.info('NVRAM configured, new values: \n\n%s\n' % self.nvram.nvram)

    def setup_loader(self, kernel_opts, overwrite=False, simulate=False):
        self.log.info('Setting up loader.conf configuration')

        with open(
            '%s/%s-current.conf' % (
                self.entry_dir, self.opsys.name
            ),
            mode='w'
        ) as entry:
            entry.write(
                'title %s %s\n' % (self.opsys.name_pretty, self.opsys.version)
            )
            entry.write(
                'linux /EFI/%s/%s-current.efi\n' % (
                    self.os_dir_name, self.opsys.kernel_name
                )
            )
            entry.write(
                'initrd /EFI/%s/%s-current\n' % (
                    self.os_dir_name, self.opsys.initrd_name
                )
            )
            entry.write('options %s\n' % kernel_opts)

        if not overwrite:
            if not os.path.exists('%s/loader.conf' % self.loader_dir):
                overwrite = True

        if overwrite:
            entry_name = '%s-current' % self.opsys.name
            with open('%s/loader.conf' % self.loader_dir, mode='w') as loader:
                default_line = 'default %s-current\n' % self.opsys.name
                loader.write(default_line)

    def copy_cmdline(self, simulate):
        self.copy_files(
            '/proc/cmdline',
            self.work_dir,
            simulate = simulate
        )

    def copy_files(self, src, dest, simulate): # Copy file src into dest
        if simulate:
            copy = ("Simulate copying " + src + " into " + dest)
            self.log.info(copy)
            return True
        else:
            try:
                shutil.copy(src, dest)
                return True
            except:
                self.log.error("Copy failed! Things may not work...")
                raise FileOpsError("Could not copy one or more files.")
                return False
