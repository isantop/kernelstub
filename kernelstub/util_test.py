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

This is a utility module for kernelstub which contains several package-wide 
functions which are useful to these 

Attributes:
    SYSTEMD_SUPPORT (bool): Whether the system supports systemd for logging.

TODO:
    * Write tests
    * Test tests
    * Add testing to app
"""

import subprocess
import unittest

from . import util

class UtilTestCase(unittest.TestCase):
    def test_systemd(self):
        try:
            systemd_supported = subprocess.run(
                ['journalctl', '--no-pager', '-n 1'], 
                check=True
            )
            # We expect the return code to be 0, which bools to false, 
            # Hence we assertNotEqual
            self.assertNotEqual(
                bool(systemd_supported.returncode),
                util.SYSTEMD_SUPPORT
            )
        except subprocess.CalledProcessError:
            self.assertFalse(util.SYSTEMD_SUPPORT)
    
    def test_clean_names(self):
        bad_name = '"This: is~a_Bad!\'<name>/\\|_?*(whee)'
        good_name = util.clean_names(bad_name)
        expected_name = 'This_is-a_Badname_whee'
        
        self.assertIs(good_name, expected_name)
    
    def test_strip_quotes(self):
        bad_string1 = '"This has quotes"'
        good_string1 = util.strip_quotes(bad_string1)
        bad_string2 = "'This has quotes'"
        good_string2 = util.strip_quotes(bad_string2)
        expected_string = 'This has quotes'

        self.assertIs(good_string1, expected_string)
        self.assertIs(good_string2, expected_string)
    
    def test_parse_options(self):
        raw_options1 = 'default="true statement" acpi.osname="Linux" nvidia-drm.modeset=1 parsed="true"'
        expected_options1 = [
            'default="true statement"', 
            'acpi.osname="Linux"', 
            'nvidia-drm.modeset=1', 
            'parsed="true"'
        ]
        clean_options1 = util.parse_options(raw_options1)

        self.assertListEqual(clean_options1, expected_options1)

        raw_options2 = [
            'these options',
            'are="wrong',
            'but"',
            'we want',
            'to',
            'test that',
            'they are not="parsed"'
        ]

        self.assertListEqual(util.parse_options(raw_options2), raw_options2)
