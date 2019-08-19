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

TODO:
    * Hook up new option flags
        > loader
"""

import os
import shutil
import sys

from . import mbconfig as config
from . import multiboot
from . import util

def replace_dict_keys(data):
    """ Replaces internally-named keys in dictionaries with human-friendly ones.
    
    Arguments: 
        data (dict): The dictionary to replace the keys in.
    
    Returns:
        An :obj:`dict` with the keys replaced.
    """
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

    This is the main object that represents the entire application.

    Arguments:
        verbosity (int, optional): How verbose program output should be. 0-2, 
            0 is less, 1 is default
        log_file_path (str, optional): Where to store the log output file.
        config_path (str, optional): Where to look for the configuration file.

    Attributes:
        args (:obj:`Namespace`): A namespace object representing the command
            line arguments.
        log (:obj:`logging.Logger`): The logging service
        config (:obj:`kernelstub.mbconfig.Systemconfiguration`): An interface 
            for getting or setting system configuration options.
    """

    def __init__(
        self,
        verbosity=1,
        log_file_path='/var/log/kernelstub.log',
        config_path='/etc/kernelstub',
        args=None,
        nosave=False):

        # Argument processing takes place in util to keep this file clean.
        loader_dir = 'loader'
        self.nosave = nosave
        self.args = util.get_args(args)
        self._no_unmount = ['/']
        
        if self.args.verbose:
            verbosity=2
        if self.args.quiet:
            verbosity=0
        if self.args.config:
            if os.path.exists(self.args.config):
                config_path = self.args.config
        if self.args.loader:
            loader_dir = self.args.loader
        if self.args.log_file:
            log_file_path = self.args.log_file

        self.log = util.setup_logging(verbosity, log_file_path)
        self.log.debug('kernelstub loaded')
            
        if os.geteuid() != 0:
            self.log.error('You need to be root or use sudo to run kernelstub')
            exit(176)
        self.log.debug('Contents of args: %s', self.args)

        self.config = config.SystemConfiguration(config_path=config_path)
        self.config.loader_dir = loader_dir
        self._no_unmount.append(self.config.esp_path)

        if self.args.preserve_live_mode and self.config.live_mode:
            # Live mode is active, warn the user and do nothing.
            self.log.error(
                'Live mode is active, no action is taken.\n\n'
                'If this is a live disk, this is probably normal and you can '
                'safely ignore this message. \n\n'
                'If this is an installed system, you should run `sudo '
                'kernelstub update` manually to get the system out of live '
                'mode and proceed with the update.'
            )
            exit(0)
        if self.args.preserve_live_mode and self.args.enable_live_mode:
            self.log.info('Enabling live mode.')
            self.config.live_mode = True
            self.log.warn(
                'All automatic kernelstub functionality has been disabled until '
                'live mode is disabled (by running kernelstub without the '
                '--preserve-live-mode flag). This means your kernel will not be '
                'automatically tracked on updates. Unless you are an OS '
                'distributor, this probably isn\'t what you want. If that '
                'applies to you, you should re-run kernelstub without the '
                '--preserve-live-mode flag to disable it.'
            )
            exit(0)
        if not self.args.preserve_live_mode and self.config.live_mode:
            self.log.info('Disabling live mode')
            self.config.live_mode = False
        if self.args.preserve_live_mode and not self.config.live_mode:
            self.log.warn(
                'Live mode is not active, --preserve-live-mode is ignored'
            )
        
        if not self.args.func:
            self.args.index = None
            self.update()
            self.lst()
            exit(0)

        if not hasattr(self, self.args.func):
            self.log.error('Unrecognized command: %s', self.args.func)
            exit(1)
        # Run the subcommand specified
        getattr(self, self.args.func)()

    def system(self):
        """ Modify system configuration."""
        if self.args.menu_timeout:
            self.config.menu_timeout = self.args.menu_timeout
        
        if self.args.esp:
            self.config.esp_path = self.args.esp_path
        
        if not self.args.quiet:
            system_config = {}
            system_config['Default Entry:'] = self.config.default_entry.split('-')[-1]
            system_config['Menu Timeout:'] = f'{self.config.menu_timeout}s'
            system_config['ESP Path:'] = self.config.esp_path

            self.log.info(
                'System configuration\n\n%s', 
                mktable(system_config, 15)
            )
    
    def create(self):
        """ Create a new entry."""
        self.log.debug('Got arguments %s', self.args)

        self.log.debug('Creating new entry')
        new_entry = multiboot.Entry()

        if self.args.index:
            new_entry.index = self.args.index
            self.log.debug('Index set to %s', new_entry.index)
        if self.args.title:
            new_entry.title = self.args.title
            self.log.debug('Title set to %s', new_entry.title)
        if self.args.mount_point:
            new_entry.drive.mount_point = self.args.mount_point
            self.log.debug('Mount point set to %s', new_entry.drive.mount_point)
        if self.args.root:
            new_entry.drive.node = self.args.root
            self.log.debug('Drive node set to %s', new_entry.drive.node)
        if self.args.exec_path:
            new_entry.exec_path = [self.args.exec_path]
            self.log.debug('Exec set to %s', new_entry.exec_path)
        if self.args.initrd_path:
            new_entry.exec_path.append(self.args.initrd_path)
            self.log.debug('Exec set to %s', new_entry.exec_path)
        if self.args.options:
            new_entry.options = self.args.options
            self.log.debug('Options set to %s', new_entry.options)
        if self.args.entry_id:
            new_entry.entry_id = self.args.entry_id
            self.log.debug('ID set to %s', new_entry.entry_id)

        if not self.nosave:
            new_entry.save_config(config_path=self.config.config_path)
            if new_entry.linux:
                if not new_entry.drive.is_mounted:
                    self.log.debug(
                        'Mounting linux entry drive %s to %s',
                        new_entry.drive.node,
                        new_entry.drive.mount_point
                    )
                    new_entry.drive.mount_drive()
            new_entry.save_entry(esp_path=self.config.esp_path)
            self.safe_unmount(new_entry.drive)

            self.log.info(
                "New entry created: %s", 
                mktable(new_entry.print_config, 15)
            )
            
            if self.args.set_default:
                self.config.default_entry = new_entry.entry_id
                self.log.info('Entry %s set as default', new_entry.index)

    def lst(self):
        """ List all entries"""
        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        self.log.debug('Got arguments %s', self.args)

        
        entry_dir = os.path.join(self.config.config_path, 'entries.d')
        if not os.path.exists(entry_dir):
            self.log.warn('No entries in %s', entry_dir)
            return
        entries = []
        for file in os.listdir(entry_dir):
            if os.path.isfile(os.path.join(entry_dir, file)):
                entry = multiboot.Entry()
                entry.load_config(config_name=file)
                entry_index = entry.index.ljust(12, '.')
                if entry.entry_id == self.config.default_entry:
                    entries.append(f'  {entry_index}{entry.title} (default)')
                else:
                    entries.append(f'  {entry_index}{entry.title}')
        self.log.info('Current Entries:\n%s', '\n'.join(entries))
        
        if self.args.index:
            try:
                entry = find_entry_from_index(self.args.index, entry_dir)
            except multiboot.EntryError as e:
                self.log.exception(e)
            
            if entry.options:
                entry.options = " ".join(entry.options)
            
            entry_table = mktable(entry.print_config, 15)
            self.log.info('%s configuration:\n%s',
                entry.title,
                entry_table
            )
    
    def update(self):
        """ Update any boot entries automatically."""
        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        self.log.debug('Got arguments %s', self.args)
        
        entry_dir = os.path.join(self.config.config_path, 'entries.d')
        if self.args.index:
            self.log.info('Updating entry with index %s', self.args.index)
            try:
                entry = find_entry_from_index(self.args.index, entry_dir)
            except multiboot.EntryError as e:
                self.log.exception(e)
            
            if entry.linux:
                if not entry.drive.is_mounted:
                    entry.drive.mount_drive(mount_point='/mnt')
            entry.save_entry(self.config.esp_path)
            self.safe_unmount(entry.drive)
        
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
        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        self.log.debug('Got arguments %s', self.args)

        entry_dir = os.path.join(self.config.config_path, 'entries.d')

        try:
            entry = find_entry_from_index(self.args.index, entry_dir)
            self.log.debug('Got entry %s', entry.entry_id)
        except multiboot.EntryError as e:
            self.log.exception(e)
        
        if self.args.title:
            entry.title = self.args.title
        if self.args.mount_point:
            entry.mount_point = self.args.root_path
        if self.args.root:
            entry.node = self.args.root
        if self.args.exec_path:
            entry.exec_path = [self.args.exec_path]
        if self.args.initrd_path:
            entry.exec_path = [entry.exec_path[0], self.args.initrd_path]
        if self.args.options:
            entry.options = self.args.options
        if self.args.add_options:
            opts = util.parse_options(self.args.add_options.split())
            for option in opts:
                if option not in entry.options:
                    entry.options.append(option)
        if self.args.delete_options:
            opts = util.parse_options(self.args.delete_options.split())
            for option in opts:
                if option in entry.options:
                    entry.options.remove(option)
        if self.args.set_default:
            self.config.default_entry = entry.entry_id
        
        entry.save_config(config_path=self.config.config_path)
        if entry.linux:
            if not entry.drive.is_mounted:
                self.log.debug(
                    'Mounting linux entry drive %s to %s',
                    entry.drive.node,
                    entry.drive.mount_point
                )
                entry.drive.mount_drive()
        entry.save_entry(esp_path=self.config.esp_path)
        self.safe_unmount(entry.drive)

        self.log.info(
            'Entry %s updated: %s', 
            entry.index, 
            mktable(entry.print_config, 15)
        )

    def delete(self):
        """ Stops updating an entry automatically, and optionally retains its
        boot configuration.
        """
        self.log.debug('Contents of sys.argv: %s', sys.argv[2:])
        self.log.debug('Got arguments %s', self.args)

        if self.args.index:
            entry_dir = os.path.join(self.config.config_path, 'entries.d')
            try:
                entry = find_entry_from_index(self.args.index, entry_dir)
            except multiboot.EntryError as e:
                self.log.exception(e)
            self.safe_unmount(entry.drive)
            
            entry_file = os.path.join(entry_dir, entry.entry_id)
            os.remove(entry_file)

            if not self.args.retain_data:
                loader_dir = os.path.join(self.config.esp_path, 'loader/entries')
                loader_file = os.path.join(loader_dir, f'{entry.entry_id}.conf')
                try:
                    os.remove(loader_file)
                except FileNotFoundError:
                    pass

                boot_dir = os.path.join(
                    self.config.esp_path,
                    'EFI',
                    entry.entry_id
                )
                try:
                    shutil.rmtree(boot_dir)
                except FileNotFoundError:
                    pass

    def safe_unmount(self, drive):
        """Unmount a drive, unless it's not safe to unmount it.
        
        Arguments:
            drive (:obj:`kernelstub.mbdrive.Drive`): A kernelstub drive object
                to potentially unmount.
        
        Returns:
            True if the drive was unmounted, otherwise False.
        """
        if not drive.mount_point in self._no_unmount:
            self.log.debug(
                '%s not in %s, unmounting...',
                drive.mount_point, 
                self._no_unmount
            )
            drive.unmount_drive()
            return True
        elif not drive.is_mounted:
            return
        return False
