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

This module contains the main Entry object for Kernelstub, which represents the 
actual boot entry on the system. 

TODO:
"""

import json
import logging
import os
import shutil
import uuid

from . import mbdrive as drive 
from . import util

class EntryError(Exception):
    """Exception used for entry errors. Pass details of the error in msg.

    Attributes: 
        msg (str): Human-readable message describing the error that threw the 
            exception.
        code (:obj:`int`, optional, default=4): Exception error code.
    
    Arguments:
        msg (str): Human-readable message describing the error that threw the 
            exception.
        code (int): Exception error code.
    """
    def __init__(self, msg, code=4):
        self.msg = msg
        self.code = code

class Entry:
    """ An object to represent a boot entry on the system. 

    Attributes:
        log (:obj:`logging.Logger`): The logging service
        drive (:obj:`kernelstub.mbdrive.Drive`) The drive object for this 
            entry's root partition.
        index (str): A short, unique, typeable reference for this entry, used 
            when manipulating entries within kernelstub. By default, we use the
            last four characters of a Type-4 (random) UUID.
        entry_id (str): This is used for identifying the entry to 
            systemd-boot, as well as naming its files on-disk. By default, it
            will be auto-generated from the entry `title` and the disk UUID.
        title (str): How the boot menu should display this entry. If
            not provided, it will be the current OS name, version, and hostname.
        linux (bool): Whether the entry is a linux-type entry or a normal
            EFI entry.
        exec_path (list): A list of paths (as :str:) to this entry's
            boot loaders. For EFI-type entries, this should be relative to the
            ESP root. For linux-style entries, this should be the path to the 
            linux kernel and the path to the initramfs image, both relative to
            the partition's mountpoint.
        options (list): A list of options to be passed to the
            executeable. Currently only used for linux-type entries. Default is
            "quiet splash"
        machine_id (str): A unique machine ID for this entry. This is either in
            /etc/machine-id, or is equal to the root-partition's UUID.
        type (str): Either 'linux' or 'efi', depending on what type of entry 
            this is.
        version (str): The version number of the linux kernel used by 
            this entry.
        config (dict): A dictionary representation of this entry's configuration.
        print_config (dict): A printable version of `config`.
    """
    def __init__(self):

        self.log = logging.getLogger('kernelstub.Entry')
        self.log.debug('Loaded kernelstub.Entry')
        self.drive = drive.Drive()
        self.drive.mount_point = '/'
        self.exec_path = ['/vmlinuz']
        self.options = "quiet splash"
    
    @property
    def index(self):
        """str: a unique, typeable index for this entry."""
        try:
            return self._index
        except AttributeError:
            idx = str(uuid.uuid4())
            idx = idx[-4:]
            self._index = idx
            return self._index
    @index.setter
    def index(self, idx):
        """Truncate to the first ten chars"""
        self._index = idx[:10]

    @property
    def entry_id(self):
        """str: a machine-parseable unique ID for this entry."""
        try: 
            return self._entry_id
        except AttributeError:
            self.entry_id = None
            return self._entry_id     
    @entry_id.setter
    def entry_id(self, e_id):
        """ If we didn't get an entry_id, generate a default from the OS name
        and machine ID. 
        """
        if not e_id:
            e_id = util.clean_names(self.title.replace(' - ', '-'))
            e_id += f'-{self.machine_id}'
            e_id += f'-{self.index}'
        self._entry_id = e_id
    
    @property
    def title(self):
        """str: The human-readable name for this entry in the boot menu."""
        try:
            return self._title
        except AttributeError:
            self.title = None
            return self._title
    @title.setter
    def title(self, title):
        """ If we didn't get a title, look it up from the current running OS."""
        if not title:
            os_name = util.get_os_name()
            os_version = util.get_os_version()
            os_hostname = util.get_hostname()
            title = f'{os_name} {os_version} ({os_hostname})'
        self._title = title     
    
    @property
    def linux(self):
        """bool: True if this is a Linux entry, otherwise False"""
        try:
            return self._linux
        except AttributeError: 
            return True
    @linux.setter
    def linux(self, linux):
        """ Only set 'linux' or 'efi', otherwise throw an exception."""
        self._linux = linux
    
    @property
    def exec_path(self):
        """:obj:`list' of :obj:`str`: The path to the executable to boot this 
        OS. If this is an efi entry, there should be one element pointing at 
        this OSs bootloader relative to the ESP. If this is a linux entry, there 
        should be two elements, one for the kernel image to boot and one for the
        initrd image (both relative to this OS's filesystem root).
        """
        try:
            return self._exec_path    
        except AttributeError:
            self._exec_path = util.detect_kernel_initrd_paths(self.mount_point)
            if self._exec_path:
                return self._exec_path
            else:
                raise EntryError(
                    'No exec path specified, and no autodetection possible. '
                    'Please specify paths manually.'
                )
    @exec_path.setter
    def exec_path(self, path):
        """ If we have one item in this list, we are doing an efi entry and 
        should set `linux` accordingly.
        """
        self._exec_path = path
        if len(path) == 1:
            if 'vmlinu' in path[0]:
                self.log.debug(
                    '%s looks like a linux kernel, looking for initrd',
                    path[0]
                )
                self.linux = True
                try:
                    auto_initrd_path = path[0].replace('vmlinuz', 'initrd.img')
                    self.log.debug('Trying %s', auto_initrd_path)
                    if os.path.exists(auto_initrd_path):
                        self._exec_path.append(auto_initrd_path)
                        self.log.debug('Initrd found at %s', auto_initrd_path)
                        return
                    self.log.debug('Couldn\'t find %s', auto_initrd_path)
                except FileNotFoundError:
                    raise EntryError(
                        f'Could not find an initrd image for kernel {path[0]}'
                    )
            self.log.debug('%s doesn\'t look like a linux kernel.', path[0])
            self.linux = False
            return
        elif len(path) == 2:
            self.log.debug(
                'Two execs supplied, kernel %s, initramfs %s',
                path[0],
                path[1]
            )
            if not os.path.exists(path[0]):
                self.log.warning(
                    'Two executables supplied, but kernel %s does not exist!',
                    path[0]
                ) 
                self.log.info('Reverting to EFI type entry.')
                self.linux = False
                self._exec_path = [path[0]]
                return
            if not os.path.exists(path[1]):
                self.log.error('Supplied initrd %s does not exist!', path[1])
                raise EntryError(f'Supplied initrd {path[1]} does not exist')
            self.linux = True
            return
        else:
            self.log.warning('Too many items in `exec_path`, got %s items.', len(path))
            self.log.warning('Try `kernelstub update %s` to save the repair.', self.index)
            self.log.info('Trying to remove the last item: %s', path[-1])
            path.pop()
            self.exec_path = path
    
    @property
    def options(self):
        """str: A string of options to 
        pass to the executable. Currently this is ignored unless the entry is a
        linux entry.
        """
        try:
            return self._options
        except AttributeError:
            return None
    @options.setter
    def options(self, options):
        """ We accept either a string  or list of options, and parse it into 
        a list.
        """
        
        if self.linux:
            self.log.debug('Setting options %s', options)
            if not options:
                options = "quiet splash"
            try:
                options.split()
                self._options = util.parse_options(options)
            #if options is a list already, there is no split()
            except AttributeError:
                self._options = options
    
    @property
    def machine_id(self):
        """str: The machine ID in /etc/machine-id, or the UUID of the drive."""
        if self.linux:
            with open(os.path.join(self.drive.mount_point, 'etc/machine-id')) as mid_file:
                return mid_file.readline().strip()
        else:
            return self.drive.uuid
    
    @property
    def type(self):
        """str: either 'linux' or 'efi'."""
        if self.linux:
            return 'linux'
        return 'efi'
    
    @property
    def version(self):
        """str: For linux type entries, try to find the kernel version number."""
        if self.linux:
            kernel_path = os.path.join(self.drive.mount_point, self.exec_path[0])
            kernel_path = os.path.realpath(kernel_path)
            return kernel_path.split('vmlinuz-')[-1]

    @property
    def mount_point(self):
        """str: The mount point of this entry's root partition."""
        if self.drive.mount_point:
            return self.drive.mount_point
        elif self.drive.node:
            self.drive.mount_point = self.drive.equate_node_mountpoint(
                self.drive.node
            )[1]
            return self.drive.mount_point
        else: 
            self.drive.mount_point = '/'
            return self.drive.mount_point
    @mount_point.setter
    def mount_point(self, mount_point):
        """We need to update the drive object, then save the config."""
        self.drive.mount_point = mount_point
    
    @property
    def node(self):
        """str: The device node path for this entry's root partition."""
        if self.drive.node:
            return self.drive.node
        elif self.drive.mount_point:
            self.drive.node = self.drive.equate_node_mountpoint(
                self.drive.mount_point
            )[0]
            return self.drive.mount_point
        else: 
            self.drive.mount_point = '/'
            return self.drive.node

        return self.drive.node
    @node.setter
    def node(self, node):
        """We need to update the drive object, then save the config."""
        self.drive.node = node

    @property
    def config(self):
        """:obj:`dict`: the configuration settings for this entry."""
        config_dict = {}
        config_dict['index'] = self.index
        config_dict['entry_id'] = self.entry_id
        config_dict['title'] = self.title
        config_dict['root_partition'] = self.drive.node
        config_dict['mount_point'] = self.drive.mount_point
        config_dict['exec_path'] = self.exec_path
        config_dict['options'] = self.options
        config_dict['config_rev'] = 4
        self.log.debug('Configuration for %s:/n%s', self._entry_id, config_dict)
        return config_dict
    
    @property
    def print_config(self):
        """:obj:`dict`: a printable version of Config."""
        print_conf = {}
        print_conf['Entry:'] = self.index
        print_conf['Title'] = self.title
        print_conf['Root Partition'] = self.node
        print_conf['Mount Point'] = self.mount_point
        if self.linux:
            kernel_realpath = os.path.realpath(self.exec_path[0])
            initrd_realpath = os.path.realpath(self.exec_path[1])
            if kernel_realpath == self.exec_path[0]:
                print_conf['Kernel'] = self.exec_path[0]
            else: 
                print_conf['Kernel'] = f'{self.exec_path[0]} => {kernel_realpath}'
            if initrd_realpath == self.exec_path[1]:
                print_conf['Initramfs'] = self.exec_path[1]
            else:
                print_conf['Initramfs'] = f'{self.exec_path[1]} => {initrd_realpath}'
            print_conf['Kernel Options'] = " ".join(self.options)
        else:
            print_conf['Loader'] = self.exec_path[0]

        print_conf['ID'] = self.entry_id
        return print_conf
    
    def save_config(self, config_path='/etc/kernelstub/'):
        """ Save this entry's configuration to disk. 

        Arguments:
            config_path (str): The path to the configuration directory to 
                save in.
        """
        self.log.debug('Saving configuration of %s', self.entry_id)
        if not os.path.exists(os.path.join(config_path, 'entries.d')):
            self.log.warning(
                'Configuration directory %s not found, creating it...',
                f'{config_path}/entries.d'
            )
            os.makedirs(os.path.join(config_path, 'entries.d'))
        self.log.debug('%s configuration: \n%s', self.index, self.config)
        config_path = os.path.join(config_path, 'entries.d', self.entry_id)
        with open(config_path, mode='w') as config_file:
            json.dump(self.config, config_file, indent=2)
            self.log.debug('Configuration saved!')
    
    def load_config(
        self, 
        config_name='kernelstub_config', 
        config_dir='/etc/kernelstub/'):
        """ Loads the configuration for this entry from the disk. 

        Arguments:
            config_name (str): The name of this entry's configuration file in
                `config_dir`
            config_dir (str): The path where entries are stored.
        """
        config_path = os.path.join(config_dir, 'entries.d', config_name)
        self.log.debug('Loading configuration from %s', config_path)

        with open(config_path) as config_file:
            config_dict = json.load(config_file)
        
        self.index = config_dict['index']
        self.node = config_dict['root_partition']
        self.mount_point = config_dict['mount_point']
        self.entry_id = os.path.basename(config_path).replace('.conf', '')
        self.exec_path = config_dict['exec_path']
        if self.linux:
            if not self.drive.is_mounted:
                self.drive.mount_drive()
            
            self.options = config_dict['options']
        
        self.title = config_dict['title']
        self.log.debug('Loaded configuration for entry %s', self.entry_id)

    def save_entry(self, esp_path, entry_dir='loader/entries'):
        """ Save the entry to the esp.
        
        Arguments:
            esp_path (str): The path to the ESP mount point.
            entry_dir (str, optional): The path of the directory on the ESP
                where entry files are stored, relative to `esp_path`. Default
                is 'loader/entries'.
        """
        self.log.debug('Saving the entry %s to disk', self.entry_id)
        
        if not os.path.exists(os.path.join(esp_path, entry_dir)):
            self.log.warning('Entry path not found, creating it.')
            os.makedirs(os.path.join(esp_path, entry_dir))
        entry_path = os.path.join(esp_path, entry_dir, f'{self.entry_id}.conf')

        # Get the paths we're going to be pointing at, and install needed files.
        exec_dests = self.install_kernel(esp_path=esp_path)
        self.log.debug('Executalble destinations: %s', exec_dests)
        entry_contents = []
        entry_contents.append('## THIS FILE IS GENERATED AUTOMATICALLY!!\n')
        entry_contents.append('## To modify this file, use `kernelstub`\n\n')
        entry_contents.append(f'title {self.title}\n')
        entry_contents.append(f'machine-id {self.machine_id}\n')
        
        # If this is a linux and we could detect the version, add it.
        if self.linux and self.version:
            self.log.debug('Got linux version: %s', self.version)
            entry_contents.append(f'version {self.version}\n')
        
        # Add in the executable to load
        entry_contents.append(f'{self.type} {exec_dests[0]}\n')
        
        if self.linux:
            real_options = [f'root=UUID={self.drive.uuid} ro']
            real_options += self.options
            entry_contents.append(f'initrd {exec_dests[1]}\n')
            entry_contents.append(f'options {" ".join(real_options)}\n')
        
        with open(entry_path, mode='w') as entry_file:
            entry_file.writelines(entry_contents)
            self.log.debug('Sucessfully saved entry to %s', entry_path)
    
    def install_kernel(
            self, 
            esp_path=None, 
            kernel_name='vmlinuz.efi', 
            init_name='initrd.img'):
        """ Installs the bootloader to the ESP and returns the paths to the 
        bootloader files.
        
        Arguments:
            esp_path (str): The path to the ESP mount point.
            kernel_name (str): The filename on the ESP that the linux kernel 
                image should use. This usually must end with '.efi'
            init_name (str): The filename on the ESP that the initramfs image
                should use. 
        
        Returns: 
            A :obj:`tuple` with the installed path of the linux image, and the
                installed path of the initrd image. Or, just the path to the 
                EFI executable (if this isn't a linux entry)
        """
        self.log.debug('Installing files to the ESP.')

        if self.linux:
            self.log.debug('Copying files for Linux installation.')
            loaders_dir = os.path.join(esp_path, 'EFI')
            dest_dir = os.path.join(loaders_dir, self.entry_id)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            # Copy the kernel
            kernel_src = os.path.join(self.drive.mount_point, self.exec_path[0])
            kernel_dest = os.path.join(dest_dir, kernel_name)
            try:
                shutil.copyfile(kernel_src, kernel_dest)
                self.log.debug(
                    'Linux copied from %s to %s.',
                    kernel_src,
                    kernel_dest
                )
            except FileNotFoundError:
                raise EntryError(
                    f'Couldn\'t copy kernel image {kernel_src}; File not found.'
                )

            # Copy the initrd image
            init_src = os.path.join(self.drive.mount_point, self.exec_path[1])
            init_dest = os.path.join(dest_dir, init_name)
            try:
                shutil.copyfile(init_src, init_dest)
                self.log.debug(
                    'Initrd copied from %s to %s.',
                    init_src,
                    init_dest
                )
            except FileNotFoundError:
                raise EntryError(
                    f'Couldn\'t copy initrd image {init_src}; File not found.'
                )

            real_options = [f'root=UUID={self.drive.uuid} ro']
            real_options += self.options
            with open(os.path.join(dest_dir, 'cmdline'), mode='w') as cmdline_file:
                cmdline_file.writelines([" ".join(real_options)])
                self.log.debug('Saved cmdline reference')
            
            return [
                kernel_dest.replace(esp_path, ''), 
                init_dest.replace(esp_path, '')
            ]
        
        else:
            self.log.debug('We aren\'t using a linux entry, nothing to do.')
            return [self.exec_path[0]]
