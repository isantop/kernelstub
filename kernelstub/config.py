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

class ConfigError(Exception):
    """Exception raised when we can't get a valid configuration."""

class Config():
    """
    Kernelstub Configuration Object

    Loads, parses and saves configuration files and parameters for
    kernelstub.
    """

    config_path = "/etc/kernelstub/configuration"
    config = {}
    config_default = {
        'default': {
            'kernel_options': ['quiet', 'splash'],
            'esp_path': "/boot/efi",
            'setup_loader': False,
            'manage_mode': False,
            'force_update' : False,
            'live_mode' : False,
            'config_rev' : 3
        }
    }

    def __init__(self, path='/etc/kernelstub/configuration'):
        self.log = logging.getLogger('kernelstub.Config')
        self.log.debug('loaded kernelstub.Config')
        self.config_path = path
        self.config = self.load_config()
        os.makedirs('/etc/kernelstub/', exist_ok=True)

    def load_config(self):
        """
        Loads a configuration from a file, or loads the default.

        If the configuration is old, it should be upgraded to a newer version.
        If the configuration file doesn't match expected conventions, try to
        correct it and warn the user about the issue.

        Returns a valid configuration dictionary.
        """
        self.log.info('Looking for configuration...')

        if os.path.exists(self.config_path):
            self.log.debug('Checking %s', self.config_path)

            with open(self.config_path) as config_file:
                self.config = json.load(config_file)

        elif os.path.exists('/etc/default/kernelstub'):
            self.log.debug('Checking fallback /etc/default/kernelstub')

            with open('/etc/default/kernelstub', mode='r') as config_file:
                self.config = json.load(config_file)

        else:
            self.log.info('No configuration file found, loading defaults.')
            self.config = self.config_default

        self.log.debug('Configuration found!')
        try:
            user_config = self.config['user']
            self.log.debug(user_config)
        except KeyError:
            self.config['user'] = self.config['default'].copy()

        try:
            self.log.debug('Configuration version: %s', self.config['user']['config_rev'])
            if self.config['user']['config_rev'] < self.config_default['default']['config_rev']:
                self.log.warning("Updating old configuration.")
                self.config = self.update_config(self.config)
                self.log.info("Configuration updated successfully!")
            elif self.config['user']['config_rev'] == self.config_default['default']['config_rev']:
                self.log.debug("Configuration up to date")
                # Double-checking in case OEMs do bad things with the config file
                if isinstance(self.config['user']['kernel_options'], str):
                    self.log.warning(
                        'Invalid kernel_options format!\n\n Usually outdated or '
                        'buggy maintainer packages from your hardware OEM. '
                        'Contact your hardware vendor to inform them to fix '
                        'their packages.'
                    )
                    try:
                        options = self.parse_options(self.config['user']['kernel_options'])
                        self.config['user']['kernel_options'] = options.split()
                    except:
                        raise ConfigError('Malformed configuration file found!')
                        exit(169)
            else:
                raise ConfigError("Configuration cannot be understood!")
        except KeyError:
            self.log.warning("Attempting upgrade of legacy configuration.")
            self.config = self.update_config(self.config)
            self.log.info("Configuration updated successfully!")
        return self.config

    def save_config(self, path='/etc/kernelstub/configuration'):
        """Saves the configuration we've used to the file."""
        self.log.debug('Saving configuration to %s', path)

        with open(path, mode='w') as config_file:
            json.dump(self.config, config_file, indent=2)

        self.log.debug('Configuration saved!')
        return 0

    def update_config(self, config):
        """Updates old configuration to a new version and returns the new one"""
        if config['user']['config_rev'] < 2:
            config['user']['live_mode'] = False
            config['default']['live_mode'] = False
        if config['user']['config_rev'] < 3:
            if isinstance(config['user']['kernel_options'], str):
                options = self.parse_options(config['user']['kernel_options'].split())
                config['user']['kernel_options'] = options
            if isinstance(config['default']['kernel_options'], str):
                options = self.parse_options(config['default']['kernel_options'].split())
                config['default']['kernel_options'] = options
        config['user']['config_rev'] = 3
        config['default']['config_rev'] = 3
        return config

    def parse_options(self, options):
        """
        Parse a list of kernel options

        Takes a list object and ensure that each item in the list is a single
        linux kernel option. Returns the resulting list.

        Positional Argument:
        options -- The list of kernel options.

        """
        self.log.debug(options)
        for index, option in enumerate(options):
            if '"' in option:
                matched = False
                itr = 1
                while matched is False:
                    try:
                        next_option = options[index + itr]
                        option = '%s %s' % (option, next_option)
                        options[index + itr] = ""
                        if '"' in next_option:
                            matched = True
                        else:
                            itr = itr + 1
                    except IndexError:
                        matched = True
            options[index] = option
        return options

    def print_config(self):
        """Returns a printable version of the configuration"""
        output_config = json.dumps(self.config, indent=2)
        return output_config
