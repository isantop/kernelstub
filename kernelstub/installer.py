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

        self.work_dir = os.path.join(self.drive.esp_path, "EFI")
        self.loader_dir = os.path.join(self.drive.esp_path, "loader")
        self.entry_dir = os.path.join(self.loader_dir, "entries")
        self.os_dir_name = "%s-%s" % (self.opsys.name, self.drive.root_uuid)
        self.os_folder = os.path.join(self.work_dir, self.os_dir_name)
        self.kernel_dest = os.path.join(self.os_folder, self.opsys.kernel_name)
        self.initrd_dest = os.path.join(self.os_folder, self.opsys.initrd_name)

        if not os.path.exists(self.loader_dir):
            os.makedirs(self.loader_dir)
        if not os.path.exists(self.entry_dir):
            os.makedirs(self.entry_dir)


    def backup_old(self, kernel_opts, setup_loader=False, simulate=False):
        self.log.info('Backing up old kernel')

        kernel_name = "%s-previous.efi" % self.opsys.kernel_name
        kernel_dest = os.path.join(self.os_folder, kernel_name)
        try:
            self.copy_files(
                '%s.old' % self.opsys.kernel_path,
                kernel_dest,
                simulate=simulate)
        except:
            pass

        initrd_name = "%s-previous" % self.opsys.initrd_name
        initrd_dest = os.path.join(self.os_folder, initrd_name)
        try:
            self.copy_files(
                '%s.old' % self.opsys.initrd_path,
                initrd_dest,
                simulate=simulate)
        except:
            pass

        if setup_loader:
            self.ensure_dir(self.entry_dir)
            linux_line = '/EFI/%s-%s/%s-previous.efi' % (self.opsys.name,
                                                         self.drive.root_uuid,
                                                         self.opsys.kernel_name)
            initrd_line = '/EFI/%s-%s/%s-previous' % (self.opsys.name,
                                                      self.drive.root_uuid,
                                                      self.opsys.initrd_name)
            self.make_loader_entry(
                self.opsys.name_pretty,
                linux_line,
                initrd_line,
                kernel_opts,
                os.path.join(self.entry_dir, '%s-oldkern' % self.opsys.name))

    def setup_kernel(self, kernel_opts, setup_loader=False, overwrite=False, simulate=False):
        self.log.info('Copying Kernel into ESP')

        self.kernel_dest = os.path.join(
            self.os_folder,
            "%s.efi" % self.opsys.kernel_name)
        self.ensure_dir(self.os_folder, simulate=simulate)

        try:
            self.copy_files(
                self.opsys.kernel_path,
                self.kernel_dest,
                simulate=simulate)

        except FileOpsError:
            self.log.critical(
                'Couldn\'t copy the kernel onto the ESP!\n' +
                'This is a critical error and we cannot continue. Check your ' +
                'settings to see if there is a typo. Otherwise, check ' +
                'permissions and try again.')
            exit(3)

        self.log.info('Copying initrd.img into ESP')

        self.initrd_dest = os.path.join(self.os_folder, self.opsys.initrd_name)
        try:
            self.copy_files(
                self.opsys.initrd_path,
                self.initrd_dest,
                simulate=simulate)

        except FileOpsError:
            self.log.critical('Couldn\'t copy the initrd onto the ESP!\n' +
                              'This is a critical error and we cannot continue. Check your settings to see if ' +
                              'there is a typo. Otherwise, check permissions and try again.')
            exit(3)

        self.log.debug('Copy complete')

        if setup_loader:
            self.log.info('Setting up loader.conf configuration')
            if not simulate:
                if not overwrite:
                    if not os.path.exists('%s/loader.conf' % self.loader_dir):
                        overwrite = True

                if overwrite:
                    self.ensure_dir(self.loader_dir)
                    entry_name = '%s-current' % self.opsys.name
                    with open('%s/loader.conf' % self.loader_dir, mode='w') as loader:
                        default_line = 'default %s-current\n' % self.opsys.name
                        loader.write(default_line)


                self.ensure_dir(self.entry_dir)
                linux_line = '/EFI/%s-%s/%s.efi' % (self.opsys.name,
                                                    self.drive.root_uuid,
                                                    self.opsys.kernel_name)
                initrd_line = '/EFI/%s-%s/%s' % (self.opsys.name,
                                                 self.drive.root_uuid,
                                                 self.opsys.initrd_name)
                self.make_loader_entry(
                    self.opsys.name_pretty,
                    linux_line,
                    initrd_line,
                    kernel_opts,
                    os.path.join(self.entry_dir, '%s-current' % self.opsys.name))

            else:
                self.log.info("Simulate creation of entry...")


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

    def copy_cmdline(self, simulate):
        self.copy_files(
            '/proc/cmdline',
            self.os_folder,
            simulate = simulate
        )


    def make_loader_entry(self, title, linux, initrd, options, filename):
        with open('%s.conf' % filename, mode='w') as entry:
            entry.write('title %s\n' % title)
            entry.write('linux %s\n' % linux)
            entry.write('initrd %s\n' % initrd)
            entry.write('options %s\n' % options)

    def ensure_dir(self, directory, simulate=False):
        if not simulate:
            try:
                os.makedirs(directory, exist_ok=True)
                return True
            except Exception as e:
                self.log.error('Couldn\'t make sure %s exists.' % directory)
                self.log.debug(e)
                return False

    def copy_files(self, src, dest, simulate): # Copy file src into dest
        if simulate:
            self.log.info('Simulate copying: %s => %s' % (src, dest))
            return True
        else:
            try:
                self.log.debug('Copying: %s => %s' % (src, dest))
                shutil.copy(src, dest)
                return True
            except Exception as e:
                self.log.debug(e)
                raise FileOpsError("Could not copy one or more files.")
                return False
