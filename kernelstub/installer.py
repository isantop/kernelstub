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
import os
import shutil

class FileOpsError(Exception):
    """Exception thrown when a file operation fails."""

class Installer():
    """
    Installer class for Kernelstub.

    Takes the information processed by kernelstub and performs the boot
    configuration and setup.
    """
    loader_dir = '/boot/efi/loader'
    entry_dir = '/boot/efi/loader/entries'
    os_dir_name = 'linux-kernelstub'
    work_dir = '/boot/efi/EFI/'
    old_kernel = True

    def __init__(self, nvram, opsys, drive):
        self.log = logging.getLogger('kernelstub.Installer')
        self.log.debug('loaded kernelstub.Installer')

        self.nvram = nvram
        self.opsys = opsys
        self.drive = drive

        self.work_dir = os.path.join(self.drive.esp_path, "EFI")
        self.loader_dir = os.path.join(self.drive.esp_path, "loader")
        self.entry_dir = os.path.join(self.loader_dir, "entries")
        self.os_dir_name = "{}-{}".format(self.opsys.name, self.drive.root_uuid)
        self.os_folder = os.path.join(self.work_dir, self.os_dir_name)
        self.kernel_dest = os.path.join(self.os_folder, self.opsys.kernel_name)
        self.initrd_dest = os.path.join(self.os_folder, self.opsys.initrd_name)

        if not os.path.exists(self.loader_dir):
            os.makedirs(self.loader_dir)
        if not os.path.exists(self.entry_dir):
            os.makedirs(self.entry_dir)


    def backup_old(self, kernel_opts, setup_loader=False, simulate=False):
        """Copy the previous kernel (if present) into the ESP."""
        self.log.info('Backing up old kernel')

        kernel_name = "{}-previous.efi".format(self.opsys.kernel_name)
        kernel_dest = os.path.join(self.os_folder, kernel_name)
        try:
            self.copy_files(
                '{}.old'.format(self.opsys.kernel_path),
                kernel_dest,
                simulate=simulate)
        except OSError:
            self.log.debug(
                'Couldn\'t back up old kernel. There\'s probably only one '
                'kernel installed.'
            )
            self.old_kernel = False

        initrd_name = "{}-previous".format(self.opsys.initrd_name)
        initrd_dest = os.path.join(self.os_folder, initrd_name)
        try:
            self.copy_files(
                '{}.old'.format(self.opsys.initrd_path),
                initrd_dest,
                simulate=simulate)
        except OSError:
            self.log.debug(
                'Couldn\'t back up old kernel. There\'s probably only one '
                'kernel installed.'
            )
            self.old_kernel = False

        if setup_loader and self.old_kernel:
            self.ensure_dir(self.entry_dir)
            linux_line = '/EFI/{}-{}/{}-previous.efi'.format(
                self.opsys.name,
                self.drive.root_uuid,
                self.opsys.kernel_name
            )
            initrd_line = '/EFI/{}-{}/{}-previous'.format(
                self.opsys.name,
                self.drive.root_uuid,
                self.opsys.initrd_name
            )
            self.make_loader_entry(
                self.opsys.name_pretty,
                linux_line,
                initrd_line,
                kernel_opts,
                os.path.join(self.entry_dir, '{}-oldkern'.format(self.opsys.name)))

    def setup_kernel(self, kernel_opts, setup_loader=False, overwrite=False, simulate=False):
        """Copy the active kernel into the ESP."""
        self.log.info('Copying Kernel into ESP')
        self.kernel_dest = os.path.join(
            self.os_folder,
            "{}.efi".format(self.opsys.kernel_name))
        self.ensure_dir(self.os_folder, simulate=simulate)
        self.log.debug('kernel being copied to %s', self.kernel_dest)

        try:
            self.copy_files(
                self.opsys.kernel_path,
                self.kernel_dest,
                simulate=simulate)

        except FileOpsError as e_e:
            self.log.exception(
                'Couldn\'t copy the kernel onto the ESP!\n'
                'This is a critical error and we cannot continue. Check your '
                'settings to see if there is a typo. Otherwise, check '
                'permissions and try again.')
            self.log.debug(e_e)
            exit(170)

        self.log.info('Copying initrd.img into ESP')
        self.initrd_dest = os.path.join(self.os_folder, self.opsys.initrd_name)
        try:
            self.copy_files(
                self.opsys.initrd_path,
                self.initrd_dest,
                simulate=simulate)

        except FileOpsError as e_e:
            self.log.exception(
                'Couldn\'t copy the initrd onto the ESP!\n This is a critical '
                'error and we cannot continue. Check your settings to see if '
                'there is a typo. Otherwise, check permissions and try again.'
            )
            self.log.debug(e_e)
            exit(171)

        self.log.debug('Copy complete')

        if setup_loader:
            self.log.info('Setting up loader.conf configuration')
            linux_line = '/EFI/{}-{}/{}-previous.efi'.format(
                self.opsys.name,
                self.drive.root_uuid,
                self.opsys.kernel_name
            )
            initrd_line = '/EFI/{}-{}/{}-previous'.format(
                self.opsys.name,
                self.drive.root_uuid,
                self.opsys.initrd_name
            )
            if simulate:
                self.log.info("Simulate creation of entry...")
                self.log.info(
                    'Loader entry: %s/%s-current\n'
                    'title %s\n'
                    'linux %s\n'
                    'initrd %s\n'
                    'options %s\n', self.entry_dir, self.opsys.name,
                    self.opsys.name_pretty, linux_line, initrd_line, kernel_opts
                )
                return 0

            if not overwrite:
                if not os.path.exists('{}/loader.conf'.format(self.loader_dir)):
                    overwrite = True

            if overwrite:
                self.ensure_dir(self.loader_dir)
                with open(
                        '{}/loader.conf'.format(self.loader_dir), mode='w'
                ) as loader:

                    default_line = 'default {}-current\n'.format(self.opsys.name)
                    loader.write(default_line)

            self.ensure_dir(self.entry_dir)
            self.make_loader_entry(
                self.opsys.name_pretty,
                linux_line,
                initrd_line,
                kernel_opts,
                os.path.join(self.entry_dir, '{}-current'.format(self.opsys.name)))

    def setup_stub(self, kernel_opts, simulate=False):
        """Set up the kernel efistub bootloader."""
        self.log.info("Setting up Kernel EFISTUB loader...")
        self.copy_cmdline(simulate=simulate)
        self.nvram.update()

        if self.nvram.os_entry_index >= 0:
            self.log.info("Deleting old boot entry")
            self.nvram.delete_boot_entry(self.nvram.order_num, simulate)

        else:
            self.log.debug("No old entry found, skipping removal.")

        self.nvram.add_entry(self.opsys, self.drive, kernel_opts, simulate)
        self.nvram.update()
        nvram_lines = "\n".join(self.nvram.nvram)
        self.log.info('NVRAM configured, new values: \n\n%s\n', nvram_lines)

    def copy_cmdline(self, simulate):
        """Copy the current boot options into the ESP."""
        self.copy_files(
            '/proc/cmdline',
            self.os_folder,
            simulate=simulate
        )


    def make_loader_entry(self, title, linux, initrd, options, filename):
        """Create a systemd-boot loader entry file."""
        self.log.info('Making entry file for %s', title)
        with open('{}.conf'.format(filename), mode='w') as entry:
            entry.write('title {}\n'.format(title))
            entry.write('linux {}\n'.format(linux))
            entry.write('initrd {}\n'.format(initrd))
            entry.write('options {}\n'.format(options))
        self.log.debug('Entry created!')

    def ensure_dir(self, directory, simulate=False):
        """Ensure that a folder exists."""
        if not simulate:
            try:
                os.makedirs(directory, exist_ok=True)
                return True
            except Exception as e_e:
                self.log.exception('Couldn\'t make sure %s exists.', directory)
                self.log.debug(e_e)
                return False

    def copy_files(self, src, dest, simulate):
        """Copy src into dest."""
        if simulate:
            self.log.info('Simulate copying: %s => %s', src, dest)
            return True
        else:
            try:
                self.log.debug('Copying: %s => %s', src, dest)
                shutil.copy(src, dest)
                return True
            except Exception as e_e:
                self.log.debug(e_e)
                raise FileOpsError("Could not copy one or more files.")
                return False
