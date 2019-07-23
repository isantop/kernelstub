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

import json
import logging
import os
import subprocess

class ConfigError(Exception):
    """Exception raised when we can't get a valid configuration."""

class UUIDNotFoundError(Exception):
    pass

class NoBlockDevError(Exception):
    pass

class Entry:

    def __init__(
        self,
        entry_id='none',
        title='none',
        root_fs=['/'],
        exec_path=['/vmlinuz', 'linux'],
        initrd_path='/initrd.img',
        options=[],
        machine_id='none',
        setup_loader=True,
        setup_nvram=False,
        in_master_config=False):
        
        """Kernelstub Entry Object
        
        Represents a boot entry on the system. 

        Params:
            entry_id (str): A system-readable name for this entry.
            title (str): A title for the entry in the boot menu.
            root_fs (:obj:`tuple` of :obj:`str`): A tuple containing the path to
                this entry partition device node, like /dev/sda1, and the 
                mountpoint for this entry's partition within the 
                current filesystem.
            kernel_path (str, optional): The path to this entry's linux image, 
                relative to root_path. Cannot be set if efi_path is set.
            initrd_path (str, optional): The path to this entry's initrd image, 
                relative to root_path. Required if kernel_path is set.
            efi_path (str, optional): The path to this entry's efi executable, 
                relative tothe ESP. Cannot be set if kernel_path is set.
            options (:obj:`list` of :obj:`str`): A list of strings as options 
                for the linux kernel. Required if kernel_path is set.
            machine_id (str): A unique identifier for the OS or partition of 
                this entry.
            setup_loader (bool): Whether to setup an entry.conf for this entry.
            setup_nvram (bool): Whether to add this entry to the system NVRAM.
            in_master_config (bool): Whether this entry is in the master 
                config file.
        """
        #: dict: A dictionary representation of the entry configuration.
        self.entry_dict = {}
        self._mtab = self.get_drives()

        self.title = title
        self.root_fs = root_fs
        self.exec_path = exec_path
        self.initrd_path = initrd_path
        self.options = options
        self.machine_id = machine_id
        self.setup_loader = setup_loader
        self.setup_nvram = setup_nvram
        self.in_master_config = in_master_config
        self.entry_id = entry_id

    @property
    def entry_id(self):
        """str: A system-readable identifier for this entry."""
        return self._entry_id
    
    @entry_id.setter
    def entry_id(self, entry_id):
        if entry_id == 'none':
            entry_id = '{name}_{id}'.format(
                name=self.clean_names(self.title),
                id=self.machine_id
            )
        self._entry_id = entry_id
    
    @property 
    def title(self):
        """str: The title of the entry in the boot menu."""
        return self._title
    
    @title.setter
    def title(self, title):
        if title == 'none':
            title = '{name} {version}'.format(
                name=self.get_os_name(),
                version=self.get_os_version()
            )
        self._title = title
        self.entry_dict['title'] = title

    @property
    def root_fs(self):
        """:obj:`tuple` of str: A tuple representing this entry's 
        root partition.
        """
        return self._root_fs
    
    @root_fs.setter 
    def root_fs(self, fs):
        if len(fs) == 1:
            dev_path = fs[0]
            dev_node = self.get_part_dev(fs[0])
        else: 
            dev_path = fs[1]
            dev_node = fs[0]

        self._root_fs = [dev_node, dev_path]
        self.entry_dict['device_path'] = dev_node
        self.entry_dict['root_path'] = dev_path
    
    @property
    def exec_path(self):
        """:obj:`tuple` of str: A tuple pointing to the executable path, and the
        executable type. If the type is 'linux', the path must point to the 
        linux kernel image path, relative to the entry's mountpoint. If it is of
        'efi' type, the path must be relative to the ESP.
        """
        return self._exec_path
    
    @exec_path.setter
    def exec_path(self, exec_path):
        self._exec_path = exec_path
        self.entry_dict['exec_path'] = exec_path[0]
        self.entry_dict['entry_type'] = exec_path[1]

    @property
    def initrd_path(self):
        """str: Path to the initrd for a "linux" type entry."""
        return self._initrd_path
    
    @initrd_path.setter
    def initrd_path(self, path):
        """Only set this if we have a 'linux' type entry."""
        if self.exec_path[1] == 'linux':
            self._initrd_path = path
            self.entry_dict['initrd_path'] = path
    
    @property
    def options(self):
        """:obj:`list` of str: A list of options to use when running 
        the executable.
        """
        return self._options
    
    @options.setter
    def options(self, options):
        self._options = options
        self.entry_dict['options'] = options
    
    @property
    def machine_id(self):
        """str: A unique id for this entry's OS. Usually either from 
        /etc/machine-id on linux, or the UUID of the entry's root partition.
        """
        return self._machine_id
    
    @machine_id.setter
    def machine_id(self, m_id):
        """If this was not provided, we need to attempt to get it from the disk
        using some other method.
        """
        if m_id == 'none':
            try:
                with open(
                    os.path.join(self.root_fs[1], 'etc/machine-id')
                ) as id_file:
                    m_id = id_file.readlines()[0].strip()
            except FileNotFoundError:
                m_id = self.get_uuid(self.root_fs[1])

        self._machine_id = m_id
        self.entry_dict['machine_id'] = m_id
    
    @property
    def setup_loader(self):
        return self._setup_loader
    
    @setup_loader.setter
    def setup_loader(self, setup):
        self._setup_loader = setup

    @property
    def setup_nvram(self):
        return self._setup_nvram
    
    @setup_nvram.setter
    def setup_nvram(self, setup):
        self._setup_nvram = setup
    
    def get_uuid(self, path):
        #self.log.debug('Looking for UUID for path %s' % path)
        try:
            args = ['findmnt', '-n', '-o', 'uuid', '--mountpoint', path]
            result = subprocess.run(args, stdout=subprocess.PIPE)
            uuid = result.stdout.decode('ASCII')
            uuid = uuid.strip()
            return uuid
        except OSError as e:
            raise UUIDNotFoundError from e
    
    def get_drives(self):
        #self.log.debug('Getting a list of drives')
        with open('/proc/mounts', mode='r') as proc_mounts:
            mtab = proc_mounts.readlines()

        #self.log.debug(mtab)
        return mtab
    
    def get_part_dev(self, path):
        #self.log.debug('Getting the block device file for %s' % path)
        for mount in self._mtab:
            drive = mount.split(" ")
            if drive[1] == path:
                part_dev = os.path.realpath(drive[0])
                #self.log.debug('%s is on %s' % (path, part_dev))
                return part_dev
        raise NoBlockDevError('Couldn\'t find the block device for %s' % path)
    
    def get_drive_dev(self, esp):
        # Ported from bash, out of @jackpot51's firmware updater
        efi_name = os.path.basename(esp)
        efi_sys = os.readlink('/sys/class/block/%s' % efi_name)
        disk_sys = os.path.dirname(efi_sys)
        disk_name = os.path.basename(disk_sys)
        #self.log.debug('ESP is a partition on /dev/%s' % disk_name)
        return disk_name
    
    def clean_names(self, name):
        """
        Remove bad characters from names.

        This is a list of characters we can't/don't want to have in technical
        names for the OS. name_pretty will still have them.
        """
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
    
    def get_os_name(self):
        """Get the current OS name."""
        os_release = self.get_os_release()
        for item in os_release:
            if item.startswith('NAME='):
                name = item.split('=')[1]
                return self.strip_quotes(name[:-1])
    
    def get_os_version(self):
        """Get the current OS version."""
        os_release = self.get_os_release()
        for item in os_release:
            if item.startswith('VERSION_ID='):
                version = item.split('=')[1]
                return self.strip_quotes(version[:-1])

    def get_os_release(self):
        """Return a list with the current OS release data."""
        try:
            with open('/etc/os-release') as os_release_file:
                os_release = os_release_file.readlines()
        except FileNotFoundError:
            os_release = [
                'NAME="{}"\n'.format(self.name),
                'ID=linux\n',
                'ID_LIKE=linux\n',
                'VERSION_ID="{}"\n'.format(self.version)
            ]

        return os_release
    def strip_quotes(self, value):
        """Return `value` without quotation marks."""
        new_value = value
        if value.startswith('"'):
            new_value = new_value[1:]
        if value.endswith('"'):
            new_value = new_value[:-1]
        return new_value
    