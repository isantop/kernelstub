#!/usr/bin/python3
"""
 kernelstub
 Comprehensive automatic ESP Management for Linux.

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

Main application
"""

import argparse
import logging
import logging.handlers as handlers
import os
import shutil
import sys

SYSTEMD_SUPPORT = False
try:
    from systemd.journal import JournalHandler
    SYSTEMD_SUPPORT = True

except ImportError:
    pass

from . import mbconfig as config
from . import multiboot
from . import util

def replace_dict_keys(data):
    """ Replaces verbose keys in data with human-friendly ones."""
    keys = {
        'index': 'Index',
        'entry_id': 'ID',
        'title': 'Title',
        'root_partition': 'Root Node',
        'mount_point': 'Mount Point',
        'exec_path': 'Loader',
        'options': 'Kernel Options',
    }

    for key in keys:
        data = data.replace(key, keys[key])
    
    return data

def find_entry_from_index(index, dir):
    """Find an entry from a given index.

    Arguments:
        index (str): The entry index to find an entry for
        dir (str): The directory to look within for the entry index.
    
    Returns:
        The :obj:`multiboot.Entry` with the supplied index.
    """
    entry_dir = dir
    for file in os.listdir(entry_dir):
        if os.path.isfile(os.path.join(entry_dir, file)):
            entry = multiboot.Entry()
            entry.load_config(file)
            if entry.index == index:
                return entry
    
    # If we fall through, raise an exception
    raise multiboot.EntryError(
        f'Couldn\'t find an entry with index {index}!'
    )

def mktable(data, padding):
    """
    Makes a printable table from a dictionary.

    returns: 
        a str containing the table.
    """

    table = '\n'
    for i in data:
        table += '  {0:{pad}} {1}\n'.format(i, data[i], pad=padding)
    return table

class Kernelstub:
    """ Main kernelstub class.

    Arguments:

    Attributes:
    """

    def __init__(
        self,
        verbosity=1,
        log_file_path='/var/log/kernelstub.log',
        config_path='/etc/kernelstub'):

        parser = argparse.ArgumentParser(
            description="Comprehensive automatic ESP Management for Linux.")
        
        parser.add_argument(
            'command',
            help='Subcommand to run'
        )
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)
    
        if os.geteuid() != 0:
            parser.print_help()
            print(
                'kernelstub:ERROR: You need to be root or use sudo to run kernelstub'
            )
            exit(176)

        level = {
            0 : logging.WARNING,
            1 : logging.INFO,
            2 : logging.DEBUG,
        }

        console_level = level[verbosity]
        file_level = level[2]

        stream_fmt = logging.Formatter(
            '%(name)-21s: %(levelname)-8s %(message)s')
        file_fmt = logging.Formatter(
            '%(asctime)s - %(name)-21s: %(levelname)-8s %(message)s')
        self.log = logging.getLogger('kernelstub')

        console_log = logging.StreamHandler()
        console_log.setFormatter(stream_fmt)
        console_log.setLevel(console_level)

        file_log = handlers.RotatingFileHandler(
            log_file_path, maxBytes=(1048576*5), backupCount=5)
        file_log.setFormatter(file_fmt)
        file_log.setLevel(file_level)

        self.log.addHandler(console_log)
        self.log.addHandler(file_log)

        if SYSTEMD_SUPPORT:
            journald_log = JournalHandler()
            journald_log.setLevel(file_level)
            journald_log.setFormatter(stream_fmt)
            self.log.addHandler(journald_log)

        self.log.setLevel(logging.DEBUG)

        self.config = config.SystemConfiguration(config_path=config_path)

        # Run the subcommand specified
        getattr(self, args.command)()

    def system(self):
        """ Modify system configuration."""
        parser = argparse.ArgumentParser(
            description='Modify system-wide configuration options')
        parser.add_argument(
            '-m',
            '--menu-timeout',
            help=(
                'The number of seconds for which to display the boot menu. '
                '0 hides the menu completely.'
            )
        )
        parser.add_argument(
            '-e',
            '--esp-path',
            help='Path to the ESP'
        )
        parser.add_argument(
            '-p',
            '--print-config',
            action='store_true',
            help='Display the current system configuration settings.'
        )
        args = parser.parse_args(sys.argv[2:])

        if args.menu_timeout:
            self.config.menu_timeout = args.menu_timeout
        
        if args.esp_path:
            self.config.esp_path = args.esp_path
        
        if args.print_config:
            system_config = {}
            system_config['Default Entry:'] = self.config.default_entry.split('-')[-1]
            system_config['Menu Timeout:'] = f'{self.config.menu_timeout}s'
            system_config['ESP Path:'] = self.config.esp_path

            print(f'System Configuration:{mktable(system_config, 15)}')
    
    def create(self):
        """ Create a new entry."""
        parser = argparse.ArgumentParser(
            description='Create a new boot entry.')
        
        parser.add_argument(
            '-n',
            '--entry-id',
            help='The new entry ID for this entry.'
        )
        parser.add_argument(
            '-t',
            '--title',
            help='The title for this entry'
        )
        parser.add_argument(
            '-r',
            '--root',
            help='Device node for the root partition'
        )
        parser.add_argument(
            '-m',
            '--mount-point',
            help='Mount point for the root partition'
        )
        parser.add_argument(
            '-e',
            '--exec-path',
            help='Path to the EFI executable or kernel image'
        )
        parser.add_argument(
            '-i',
            '--initrd-path',
            help='Path to the initrd image (for linux entries)'
        )
        parser.add_argument(
            '-o',
            '--options',
            help='Linux Kernel command line options for this entry.'
        )
        parser.add_argument(
            '-x',
            '--index',
            help='An optional index for the new entry.'
        )
        parser.add_argument(
            '-s',
            '--set-default',
            help='Set this new entry as the default boot entry'
        )
        args = parser.parse_args(sys.argv[2:])

        kwargs = {}

        if args.entry_id:
            kwargs['entry_id'] = args.entry_id
        if args.title:
            kwargs['title'] = args.title
        if args.mount_point:
            kwargs['mount_point'] = args.mount_point
        if args.root:
            kwargs['node'] = args.root
        if args.exec_path:
            kwargs['exec_path'] = [args.exec_path]
        if args.initrd_path:
            kwargs['exec_path'].append(args.initrd_path)
        if args.options:
            kwargs['options'] = args.options
        if args.index:
            kwargs['index'] = args.index
        
        self.log.debug('Got arguments %s', args)
        self.log.debug('Passing args to new entry: %s', kwargs)

        new_entry = multiboot.Entry(**kwargs)

        new_entry.save_config(config_path=self.config.config_path)
        new_entry.save_entry(esp_path=self.config.esp_path)

        self.log.info(
            "New entry created: %s", 
            mktable(new_entry.print_config, 15)
        )
        
        if args.set_default:
            self.config.default_entry = new_entry.entry_id
            self.log.info('Entry %s set as default', new_entry.index)

    def list(self):
        """ List all entries"""
        parser = argparse.ArgumentParser(
            description='List all entries and their indicies')
        parser.add_argument(
            'index',
            nargs='?',
            help='List details of an entry index'
        )

        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        args = parser.parse_args(sys.argv[2:])
        self.log.debug('Got arguments %s', args)

        
        entry_dir = os.path.join(self.config.config_path, 'entries.d')
        if not os.path.exists(entry_dir):
            self.log.warn('No entries in %s', entry_dir)
            return
        print("Current Entries:\n")
        for file in os.listdir(entry_dir):
            if os.path.isfile(os.path.join(entry_dir, file)):
                entry = multiboot.Entry()
                entry.load_config(config_name=file)
                entry_index = entry.index.ljust(12, '.')
                print(f'  {entry_index}{entry.title}')
        
        if args.index:
            try:
                entry = find_entry_from_index(args.index, entry_dir)
            except multiboot.EntryError as e:
                self.log.exception(e)
            
            entry.options = " ".join(entry.options)
            #entry.exec_path = " , initrd: ".join(entry.exec_path)
            
            entry_table = mktable(entry.print_config, 15)
            print(entry_table)
    
    def update(self):
        """ Update any boot entries automatically."""
        parser = argparse.ArgumentParser(
            description='Update any boot entries automatically')
        
        parser.add_argument(
            'index',
            nargs='?',
            help='The entry index to update'
        )

        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        args = parser.parse_args(sys.argv[2:])
        self.log.debug('Got arguments %s', args)
        
        entry_dir = os.path.join(self.config.config_path, 'entries.d')
        if args.index:
            self.log.info('Updating entry with index %s', args.index)
            try:
                entry = find_entry_from_index(args.index, entry_dir)
            except multiboot.EntryError as e:
                self.log.exception(e)
            
            if not entry.drive.is_mounted:
                entry.drive.mount_drive(mount_point='/mnt')
            entry.save_entry(esp_path=self.config.esp_path)
            if not entry.drive.mount_point == '/':
                entry.drive.unmount_drive()
        
        else:
            self.log.info('Updating all entries')
            for file in os.listdir(entry_dir):
                if os.path.isfile(os.path.join(entry_dir, file)):
                    entry = multiboot.Entry()
                    entry.load_config(config_name=file)
                    if not entry.drive.is_mounted:
                        entry.drive.mount_drive(mount_point='/mnt')
                    entry.save_entry(esp_path=self.config.esp_path)
                    if not entry.drive.mount_point == '/':
                        entry.drive.unmount_drive()
    
    def edit(self):
        """ Modify an entry, and then save it to disk."""
        parser = argparse.ArgumentParser(
            description='Modify an entry and save it to disk')
        
        parser.add_argument(
            'index',
            help='The entry index to modify; use `list` for a list.'
        )
        parser.add_argument(
            '-n',
            '--entry-id',
            help='The new entry ID for this entry.'
        )
        parser.add_argument(
            '-t',
            '--title',
            help='The title for this entry'
        )
        parser.add_argument(
            '-r',
            '--root',
            help='Device node for the root partition'
        )
        parser.add_argument(
            '-m',
            '--mount-point',
            help='Mount point for the root partition'
        )
        parser.add_argument(
            '-e',
            '--exec-path',
            help='Path to the EFI executable or kernel image'
        )
        parser.add_argument(
            '-i',
            '--initrd-path',
            help='Path to the initrd image (for linux entries)'
        )
        parser.add_argument(
            '-o',
            '--options',
            help='Linux Kernel command line options for this entry'
        )
        parser.add_argument(
            '-a',
            '--add-options',
            help='Add new options without affecting existing options'
        )
        parser.add_argument(
            '-d',
            '--delete-options',
            help='Remove select options without affecting other options'
        )
        parser.add_argument(
            '-s',
            '--set-default',
            action='store_true',
            help='Set this new entry as the default boot entry'
        )
        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        args = parser.parse_args(sys.argv[2:])
        self.log.debug('Got arguments %s', args)

        entry_dir = os.path.join(self.config.config_path, 'entries.d')
        try:
            entry = find_entry_from_index(args.index, entry_dir)
        except multiboot.EntryError as e:
            self.log.exception(e)
        
        if args.title:
            entry.title = args.title
        if args.mount_point:
            entry.drive.mount_point = args.root_path
        if args.root:
            entry.drive.node = args.root
        if args.exec_path:
            entry.exec_path = [args.exec_path]
        if args.initrd_path:
            entry.exec_path.append(args.initrd_path)
        if args.options:
            entry.options = args.options
        
        if args.add_options:
            opts = util.parse_options(args.add_options.split())
            for option in opts:
                if option not in entry.options:
                    entry.options.append(option)
        
        if args.delete_options:
            opts = util.parse_options(args.delete_options.split())
            for option in opts:
                if option in entry.options:
                    entry.options.remove(option)
        
        if args.set_default:
            self.config.default_entry = entry.entry_id
        
        entry.save_config(config_path=self.config.config_path)
        entry.save_entry(esp_path=self.config.esp_path)

        self.log.info(
            'Entry %s updated: %s', 
            entry.index, 
            mktable(entry.print_config, 15)
        )

    def delete(self):
        """ Stops updating an entry automatically, and optionally retains its
        boot configuration.
        """
        parser = argparse.ArgumentParser(
            description='Delete an entry from kernelstub')
        
        parser.add_argument(
            'index',
            help='The entry index to delete; use `list` for a list.'
        )
        parser.add_argument(
            '-r',
            '--retain-entry',
            action='store_true',
            help='Keeps the entry boot configuration in the bootmenu.'
        )

        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        args = parser.parse_args(sys.argv[2:])
        self.log.debug('Got arguments %s', args)

        if args.index:
            entry_dir = os.path.join(self.config.config_path, 'entries.d')
            try:
                entry = find_entry_from_index(args.index, entry_dir)
            except multiboot.EntryError as e:
                self.log.exception(e)
            
            entry_file = os.path.join(entry_dir, entry.entry_id)
            os.remove(entry_file)

            if not args.retain_entry:
                loader_dir = os.path.join(self.config.esp_path, 'loader/entries')
                loader_file = os.path.join(loader_dir, f'{entry.entry_id}.conf')
                os.remove(loader_file)

                boot_dir = os.path.join(
                    self.config.esp_path,
                    'EFI',
                    entry.entry_id
                )
                shutil.rmtree(boot_dir)


