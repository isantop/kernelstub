#!/usr/bin/python3

"""
 kernelstub Version 0.2

 The automatic manager for using the Linux Kernel EFI Stub to boot

 Copyright 2017 Ian Santopietro <isantop@gmail.com>

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
"""

import yaml, os

class Config():

    config_path = "/etc/default/kernelstub"
    config = {}
    config_default = {'default': {'kernel_options': 'quiet splash',
                                  'manage_mode': False,
                                  'force_update': False,},
                      }

    def __init__(self, path='/etc/default/kernelstub'):
        self.config_path = path
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path) as config_file:
                self.config = yaml.safe_load(config_file)
        else:
            self.config = self.config_default

        return self.config

        
