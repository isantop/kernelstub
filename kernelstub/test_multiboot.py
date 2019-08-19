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

This is a unit testcase for the multiboot module

TODO:
    * Write tests
    * Test tests
"""

import os
import platform
import unittest

from . import multiboot

def get_linux_path():
    paths = [
        '/vmlinuz',
        '/boot/vmlinuz'
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return False

def get_initrd_path():
    paths = [
        '/initrd.img',
        '/boot/initrd.img'
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return False

def checkAmLinux():
    if get_linux_path() and get_initrd_path():
        return True
    return False

class EntryTestCase(unittest.TestCase):
    def setUp(self):
        self.entry = multiboot.Entry()
        self.entry.title = "Testing!_Entry~1.0"
    
    def setLinux(self, linux):
        if linux:
            self.entry.exec_path = [get_linux_path(), get_initrd_path()]
        else:
            self.entry.exec_path = ['/EFI/notlinux/notlinux64.efi']

    
    def test_entryid(self):
        self.assertTrue('Testing_Entry-1.0' in self.entry.entry_id)

    def test_linux(self):
        self.setLinux(False)
        self.assertFalse(self.entry.linux)

        if checkAmLinux():
            self.setLinux(True)
            self.assertTrue(self.entry.linux)
    
    @unittest.skipUnless(checkAmLinux(), 'Can\'t test linux on non-linux')
    def test_options(self):
        self.setLinux(True)
        self.entry.options = 'default="true statement" acpi.osname="Linux" nvidia-drm.modeset=1 parsed="true"'
        expected_options = [
            'default="true statement"', 
            'acpi.osname="Linux"', 
            'nvidia-drm.modeset=1', 
            'parsed="true"'
        ]

        self.assertEqual(expected_options, self.entry.options)

    def test_type(self):
        self.setLinux(False)
        self.assertEqual('efi', self.entry.type)

        if checkAmLinux():
            self.setLinux(True)
            self.assertEqual('linux', self.entry.type)
    
    @unittest.skipUnless(checkAmLinux(), 'Can\'t test linux on non-linux')
    def test_version(self):
        self.setLinux(True)
        thisver = platform.uname().release
        self.assertEqual(thisver, self.entry.version)
