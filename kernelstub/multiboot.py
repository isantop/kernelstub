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
"""

import json
import logging
import os
import shutil
import subprocess

from . import mbdrive 
from . import util
from . import mbopsys

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

    Arguments: 
    """
    def __init__(
            self,
            entry_id=None,
            title=None,
            mount_point='/',
            node=None,
            exec_path=['/vmlinuz', '/initrd.img'],
            options=None):
        self.exec_path = exec_path
        self.drive = mbdrive.Drive(node=node, mount_point=mount_point)
        if self.linux:
            if not self.drive.is_mounted:
                self.drive.mount_drive()
        
        self.title = title
        self.entry_id = entry_id
        self.options = options

    @property
    def entry_id(self):
        """str: a machine-parseable unique ID for this entry."""
        return self._entry_id

    @entry_id.setter
    def entry_id(self, e_id):
        """ If we didn't get an entry_id, generate a default from the OS name
        and machine ID. 
        """
        if not e_id:
            e_id = util.clean_names(self.title.replace(' - ', '-'))
            e_id += f'-{self.machine_id}'
        self._entry_id = e_id
    
    @property
    def title(self):
        """str: The human-readable name for this entry in the boot menu."""
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
        return self._linux
    
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
        return self._exec_path
    
    @exec_path.setter
    def exec_path(self, path):
        """ If we have one item in this list, we are doing an efi entry and 
        should set `linux` accordingly.
        """
        self._exec_path = path
        if len(path) == 1:
            self.linux = False
        elif len(path) == 2:
            self.linux = True
        else:
            raise EntryError(
                f'Too many items in `exec_path`, got {str(len(path))} items.'
            )
    
    @property
    def options(self):
        """:obj:`list` of :obj:`str`: A list containing strings of options to 
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
            if not options:
                options = "quiet splash"
            try:
                self._options = util.parse_options(options.split())
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
    def config(self):
        """:obj:`dict`: the configuration settings for this entry."""
        config_dict = {}
        config_dict['title'] = self.title
        config_dict['root_partition'] = self.drive.node
        config_dict['mount_point'] = self.drive.mount_point
        config_dict['exec_path'] = self.exec_path
        config_dict['options'] = self.options
        config_dict['config_rev'] = 4
        return config_dict
    
    def save_config(self, config_path='/etc/kernelstub/entries.d'):
        """ Save this entry's configuration to disk. 

        Arguments:
            config_path (str): The path to the configuration directory to 
                save in.
        """
        path = os.path.join(config_path, self.entry_id)
        with open(path, mode='w') as config_file:
            json.dump(self.config, config_file, indent=2)
    
    def load_config(
        self, 
        config_name='kernelstub_config', 
        config_dir='/etc/kernelstub/entries.d'):
        """ Loads the configuration for this entry from the disk. 
        """
        config_path = os.path.join(config_dir, config_name)

        with open(config_path) as config_file:
            config_dict = json.load(config_file)
        
        self.entry_id = os.path.basename(config_path).replace('.conf', '')
        self.exec_path = config_dict['exec_path']
        if self.linux:
            node = config_dict['root_partition']
            mount_point = config_dict['mount_point']
            self.drive = mbdrive.Drive(node=node, mount_point=mount_point)
            if not self.drive.is_mounted:
                self.drive.mount_drive()
            
            self.options = config_dict['options']
        
        self.title = config_dict['title']


    def save_entry(self, esp_path='/boot/efi', entry_dir='loader/entries'):
        """ Save the entry to the esp."""
        entry_path = os.path.join(esp_path, entry_dir, f'{self.entry_id}.conf')

        # Get the paths we're going to be pointing at, and install needed files.
        exec_dests = self.install_kernel(esp_path=esp_path)
        
        entry_contents = []
        entry_contents.append('## THIS FILE IS GENERATED AUTOMATICALLY!!\n')
        entry_contents.append('## To modify this file, use `kernelstub`\n\n')
        entry_contents.append(f'title {self.title}\n')
        entry_contents.append(f'machine-id {self.machine_id}\n')
        
        # If this is a linux and we could detect the version, add it.
        if self.linux and self.version:
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
    
    def install_kernel(
            self, 
            esp_path='/boot/efi', 
            kernel_name='vmlinuz.efi', 
            init_name='initrd.img'):
        """ If this is a linux entry, install the kernel to the ESP."""
        if self.linux:
            esp_dest_path = os.path.join(esp_path, 'EFI')
            dest_dir = os.path.join(esp_dest_path, self.entry_id)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            # Copy the kernel
            kernel_src = os.path.join(self.drive.mount_point, self.exec_path[0])
            kernel_dest = os.path.join(dest_dir, kernel_name)
            shutil.copyfile(kernel_src, kernel_dest)

            # Copy the initrd image
            init_src = os.path.join(self.drive.mount_point, self.exec_path[1])
            init_dest = os.path.join(dest_dir, init_name)
            shutil.copyfile(init_src, init_dest)

            real_options = [f'root=UUID={self.drive.uuid} ro']
            real_options += self.options
            with open(os.path.join(dest_dir, 'cmdline'), mode='w') as cmdline_file:
                cmdline_file.writelines([" ".join(real_options)])
            
            return [
                kernel_dest.replace(esp_path, ''), 
                init_dest.replace(esp_path, '')
            ]
        
        else:
            return [self.exec_path[0]]
