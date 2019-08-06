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

import platform

def get_os_release():
    """Return a list with the current OS release data."""
    try:
        with open('/etc/os-release') as os_release_file:
            os_release = os_release_file.readlines()
    except FileNotFoundError:
        pass

    return os_release

def clean_names(name):
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

def strip_quotes(value):
    """Return `value` without quotation marks."""
    new_value = value
    if value.startswith('"'):
        new_value = new_value[1:]
    if value.endswith('"'):
        new_value = new_value[:-1]
    return new_value

class OS():
    """
    Kernelstub OS object.

    Provides helper functions for getting and storing OS information.
    """

    @property 
    def name_pretty(self):
        """str: The current OS name."""
        os_release = get_os_release()
        for item in os_release:
            if item.startswith('NAME='):
                name = item.split('=')[1]
                return strip_quotes(name[:-1])
    
    @property
    def name(self):
        """str: A machine-friendly, sanitized description of the OS Name."""
        return clean_names(self.name_pretty)
    
    @property
    def version(self):
        """str: The current OS version number."""
        os_release = get_os_release()
        for item in os_release:
            if item.startswith('VERSION_ID='):
                version = item.split('=')[1]
                return strip_quotes(version[:-1])
    
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