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

Please see the provided LICENCE.txt file for additional distribution/copyright
terms.
"""

import json, os, logging

class Config():

    config_path = "/etc/kernelstub/configuration"
    config = {}
    config_default = {
        'default': {
            'kernel_options': 'quiet splash',
            'esp_path': "/boot/efi",
            'setup_loader': False,
            'manage_mode': False,
            'force_update' : False
        }
    }

    def __init__(self, path='/etc/kernelstub/configuration'):
        self.log = logging.getLogger('kernelstub.Config')
        self.log.debug('Logging set up')
        self.log.debug('loaded kernelstub.Config')
        self.config_path = path
        self.config = self.load_config()
        os.makedirs('/etc/kernelstub/', exist_ok=True)

    def load_config(self):
        self.log.info('Looking for configuration...')

        if os.path.exists(self.config_path):
            self.log.debug('Checking %s' % self.config_path)

            with open(self.config_path) as config_file:
                self.config = json.load(config_file)

        elif os.path.exists('/etc/default/kernelstub/'):
            self.log.debug('Checking fallback /etc/default/kernelstub')

            with open('/etc/default/kernelstub', mode='r') as config_file:
                self.config = json.load(config_file)

        else:
            self.log.info('No configuration file found, loading defaults.')
            self.config = self.config_default
            self.config['user'] = self.config['default'].copy()

        self.log.info('Configuration found!')
        return self.config

    def save_config(self, path='/etc/kernelstub/configuration'):
        self.log.debug('Saving configuration...')

        with open(path, mode='w') as config_file:
            json.dump(self.config, config_file, indent=2)
        
        self.log.info('Configuration saved!')
        return 0

    def print_config(self):
        output_config = json.dumps(self.config, indent=2)
        return output_config
