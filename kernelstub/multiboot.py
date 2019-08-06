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

from . import mbdrive 
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
        if self.linux:
            self.drive = mbdrive.Drive(node=node, mount_point=mount_point)
            if not self.drive.is_mounted:
                self.drive.mount_drive()
        
        self.entry_id = entry_id
        self.title = title
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
            e_id = util.clean_names(self.title)
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
            self._title = f'{util.get_os_name()} {util.get_os_version}'
    
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
        return self._options
    
    @options.setter
    def options(self, options):
        """ We accept either a string  or list of options, and parse it into 
        a list.
        """
        if self.linux:
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