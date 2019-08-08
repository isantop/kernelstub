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

import platform

from . import util

class OS():
    """
    Kernelstub OS object.

    Provides helper functions for getting and storing OS information.
    """

    @property 
    def name_pretty(self):
        """str: The current OS name."""
        os_release = util.get_os_release()
        for item in os_release:
            if item.startswith('NAME='):
                name = item.split('=')[1]
                return util.strip_quotes(name[:-1])
    
    @property
    def name(self):
        """str: A machine-friendly, sanitized description of the OS Name."""
        return util.clean_names(self.name_pretty)
    
    @property
    def version(self):
        """str: The current OS version number."""
        os_release = util.get_os_release()
        for item in os_release:
            if item.startswith('VERSION_ID='):
                version = item.split('=')[1]
                return util.strip_quotes(version[:-1])
    
    @property
    def hostname(self):
        """str: The current OS hostname."""
        return platform.node()
    
    @property
    def mtab(self):
        """:obj`dict`: A list of partitions on the system."""
        with open('/proc/mounts') as proc_mounts:
            mtab_list = proc_mounts.readlines()
        mtab = {}
        for partition in mtab_list:
            unparsed = partition.split()
            parsed = {}
            parsed['node'] = unparsed[0]
            parsed['mountpoint'] = unparsed[1]
            parsed['type'] = unparsed[2]
            parsed['options'] = unparsed[3]
            mtab[unparsed[0]] = parsed
        return mtab