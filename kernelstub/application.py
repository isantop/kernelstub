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

 This program will automatically keep a copy of the Linux Kernel image and your
 initrd.img located on your EFI System Partition (ESP) on an EFI-compatible
 system. The benefits of this approach include being able to boot Linux directly
 and bypass the GRUB bootloader in many cases, which can save 4-6 seconds during
 boot on a system with a fast drive. Please note that there are no guarantees
 about boot time saved using this method.

 For maximum safety, kernelstub recommends leaving an entry for GRUB in your
 system's ESP and NVRAM configuration, as GRUB allows you to modify boot
 parameters per-boot, which loading the kernel directly cannot do. The only
 other way to do this is to use an EFI shell to manually load the kernel and
 give it parameters from the EFI Shell. You can do this by using:

 fs0:> vmlinuz-image initrd=EFI/path/to/initrd/stored/on/esp options

 kernelstub will load parameters from the /etc/default/kernelstub config file.
"""

import logging
import logging.handlers as handlers
import os

from . import drive as Drive
from . import nvram as Nvram
from . import opsys as Opsys
from . import installer as Installer
from . import config as Config

SYSTEMD_SUPPORT = False
try:
    from systemd.journal import JournalHandler
    SYSTEMD_SUPPORT = True

except ImportError:
    pass

class CmdLineError(Exception):
    """ Exception raised when we can't find any kernel parameters """

class Kernelstub():
    """ Main Kernelstub Class """

    def mktable(self, data, padding):
        """
        Makes a table from a dictionary.

        returns: a str containing the table.
        """
        table = ''
        for i in data:
            table += '    {0:{pad}} {1}\n'.format(i, data[i], pad=padding)
        return table

    def main(self, args):
        """ Do the thing """
        log_file_path = '/var/log/kernelstub.log'
        if args.log_file:
            log_file_path = args.log_file

        verbosity = 0
        if args.verbosity:
            verbosity = args.verbosity
        if verbosity > 2:
            verbosity = 2

        if args.print_config:
            verbosity = 1

        level = {
            0 : logging.WARNING,
            1 : logging.INFO,
            2 : logging.DEBUG,
        }

        console_level = level[verbosity]
        file_level = level[2]

        stream_fmt = logging.Formatter(
            '%(name)-21s: %(levelname)-8s %(message)s')
        file_fmt = logging.Formatter(
            '%(asctime)s - %(name)-21s: %(levelname)-8s %(message)s')
        log = logging.getLogger('kernelstub')

        console_log = logging.StreamHandler()
        console_log.setFormatter(stream_fmt)
        console_log.setLevel(console_level)

        file_log = handlers.RotatingFileHandler(
            log_file_path, maxBytes=(1048576*5), backupCount=5)
        file_log.setFormatter(file_fmt)
        file_log.setLevel(file_level)

        log.addHandler(console_log)
        log.addHandler(file_log)

        if SYSTEMD_SUPPORT:
            journald_log = JournalHandler()
            journald_log.setLevel(file_level)
            journald_log.setFormatter(stream_fmt)
            log.addHandler(journald_log)

        log.setLevel(logging.DEBUG)

        log.debug('Got command line options: %s', args)

        # Figure out runtime options
        no_run = False
        if args.dry_run:
            no_run = True

        config = Config.Config()
        configuration = config.config['user']

        if args.esp_path:
            configuration['esp_path'] = args.esp_path

        root_path = "/"
        if args.root_path:
            root_path = args.root_path

        opsys = Opsys.OS()

        if args.kernel_path:
            log.debug('Manual kernel path:\n %s', args.kernel_path)
            opsys.kernel_path = args.kernel_path
        else:
            opsys.kernel_path = os.path.join(root_path, opsys.kernel_name)

        if args.initrd_path:
            log.debug('Manual initrd path:\n %s', args.initrd_path)
            opsys.initrd_path = args.initrd_path
        else:
            opsys.initrd_path = os.path.join(root_path, opsys.initrd_name)

        if not os.path.exists(opsys.kernel_path):
            log.exception(
                'Can\'t find the kernel image! \n\n Please use the '
                '--kernel-path option to specify the path to the kernel image'
            )
            exit(0)

        if not os.path.exists(opsys.initrd_path):
            log.exception(
                'Can\'t find the initrd image! \n\n Please use the '
                '--initrd-path option to specify the path to the initrd image'
            )
            exit(0)

        # Check for kernel parameters. Without them, stop and fail
        if args.k_options:
            configuration['kernel_options'] = config.parse_options(args.k_options.split())
        else:
            try:
                configuration['kernel_options']
            except KeyError:
                error = (
                    'cmdline was "InvalidConfig"\n\n Could not find any valid '
                    'configuration. This probably means that the configuration '
                    'file is corrupt. Either remove it to regenerate it from '
                    'default or fix the existing one.'
                )
                log.exception(error)
                raise CmdLineError("No Kernel Parameters found")
                exit(168)

        log.debug(config.print_config())

        if args.preserve_live and configuration['live_mode']:
            configuration['live_mode'] = True
            log.warning(
                'Live mode is enabled!\n'
                'Kernelstub is running in live environment mode. This usually '
                'means that you are running a live disk, and kernelstub should '
                'not run. We are thus exiting with 0.\n'
                'If you are not running a live disk, please run '
                '`sudo kernelstub` to disable live mode.'
            )
            exit(0)

        configuration['live_mode'] = False

        if args.setup_loader:
            configuration['setup_loader'] = True
        if args.off_loader:
            configuration['setup_loader'] = False

        if args.install_stub:
            configuration['manage_mode'] = False
        if args.manage_mode:
            configuration['manage_mode'] = True


        log.debug('Checking configuration integrity...')
        try:
            kernel_opts = configuration['kernel_options']
            esp_path = configuration['esp_path']
            setup_loader = configuration['setup_loader']
            manage_mode = configuration['manage_mode']
            force = configuration['force_update']
            live_mode = configuration['live_mode']

        except KeyError:
            log.exception(
                'Malformed configuration! \n'
                'The configuration we got is bad, and we can\'nt continue. '
                'Please check the config files and make sure they are correct. '
                'If you can\'t figure it out, then deleting them should fix '
                'the errors and cause kernelstub to regenerate them from '
                'Default. \n\n You can use "-vv" to get the configuration used.')
            log.debug('Configuration we got: \n\n%s', config.print_config())
            exit(169)


        if args.add_options:
            add_opts = args.add_options.split(" ")
            add_opts = config.parse_options(add_opts)
            for opt in add_opts:
                if opt not in kernel_opts:
                    kernel_opts.append(opt)
                    configuration['kernel_options'] = kernel_opts

        if args.remove_options:
            rem_opts = args.remove_options.split(" ")
            rem_opts = config.parse_options(rem_opts)
            kernel_opts = list(set(kernel_opts) - set(rem_opts))
            configuration['kernel_options'] = kernel_opts

        if args.force_update:
            force = True
        if configuration['force_update'] is True:
            force = True

        log.debug('Structing objects')

        drive = Drive.Drive(root_path=root_path, esp_path=esp_path)
        nvram = Nvram.NVRAM(opsys.name, opsys.version)
        installer = Installer.Installer(nvram, opsys, drive)

        # Log some helpful information, to file and optionally console
        data_system = {
            'Root:': drive.root_fs,
            'ESP:': drive.esp_fs,
            'Kernel Path:': opsys.kernel_path,
            'Initrd Path:': opsys.initrd_path,
            'Boot Options:': " ".join(kernel_opts),
        }
        data_debug = {
            'OS:': "{} {}".format(opsys.name_pretty, opsys.version),
            'ESP Partition #:': drive.esp_num,
            'NVRAM entry #:': nvram.os_entry_index,
            'Boot Variable #:': nvram.order_num,
            'Root FS UUID:': drive.root_uuid,
        }
        data_config = {
            'Kernel Options:': " ".join(kernel_opts),
            'ESP Path:': esp_path,
            'Install loader config:': setup_loader,
            'Management Mode:': manage_mode,
            'Force Overwrite:': str(force),
            'Live Disk Mode:': live_mode,
            'Config revision:': configuration['config_rev']
        }
        if args.print_config:
            log.info(
                'System information:\n\n%s', self.mktable(data_system, 22)
            )
            log.debug(
                'Debug information:\n\n%s', self.mktable(data_debug, 22)
            )
            log.info(
                'Active configuration details:\n\n%s',
                self.mktable(data_config, 22)
            )
            exit(0)

        log.info(
            'System information:\n\n%s', self.mktable(data_system, 16)
        )
        log.debug(
            'Debug information:\n\n%s', self.mktable(data_debug, 16)
        )
        log.debug(
            'Active configuration:\n\n%s', self.mktable(data_config, 22)
        )

        if args.print_config:
            log.info(
                'Active configuration details:\n\n%s',
                self.mktable(data_config, 22)
            )
            exit(0)

        log.debug('Setting up boot...')

        kopts = 'root=UUID={uuid} ro {options}'.format(
            uuid=drive.root_uuid,
            options=" ".join(kernel_opts)
        )
        log.debug('kopts: %s', kopts)



        installer.setup_kernel(
            kopts,
            setup_loader=setup_loader,
            overwrite=force,
            simulate=no_run)
        try:
            installer.backup_old(
                kopts,
                setup_loader=setup_loader,
                simulate=no_run)
        except Exception as e_e:
            log.debug(
                'Couldn\'t back up old kernel. \nThis might just mean you '
                'don\'t have an older kernel installed. If you do, try with -vv'
                ' to see debugging information'
            )
            log.debug(e_e)

        installer.copy_cmdline(simulate=no_run)

        if not manage_mode:
            installer.setup_stub(kopts, simulate=no_run)

        log.debug('Saving configuration to file')

        config.config['user'] = configuration
        config.save_config()

        log.debug('Setup complete!\n\n')

        return 0
