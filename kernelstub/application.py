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

import logging, subprocess, shutil, os, platform

from . import drive as Drive
from . import nvram as Nvram
from . import opsys as Opsys
from . import installer as Installer
from . import config as Config

class CmdLineError(Exception):
    pass

class Kernelstub():

    def main(self, args): # Do the thing

        file_level = 'INFO'

        verbosity = 0
        if args.verbosity:
            verbosity = args.verbosity
        if verbosity > 2:
            verbosity = 2

        level = {
            0 : 'WARNING',
            1 : 'INFO',
            2 : 'DEBUG',
        }

        console_level = level[verbosity]

        log = logging.getLogger('kernelstub')
        console = logging.StreamHandler()
        stream_fmt = logging.Formatter('%(name)-21s: %(levelname)-8s %(message)s')
        console.setFormatter(stream_fmt)
        log.addHandler(console)
        log.setLevel(console_level)
        log.debug('Logging set up')

        # Figure out runtime options
        no_run = False
        if args.dry_run:
            no_run = True

        config = Config.Config()

        configuration = config.config['user']

        if args.esp_path:
            configuration['esp_path'] = args.esp_path

        opsys = Opsys.OS()

        if args.kernel_path:
            log.debug(
                'Manually specified kernel path:\n ' +
                '                                %s' % args.kernel_path
            )
            kernel_path = args.kernel_path
        else:
            log.debug("No kernel specified, attempting automatic discovery")
            kernel_path = "/boot/%s-%s" % (opsys.kernel_name, opsys.kernel_release)

        if not os.path.exists(kernel_path):
            log.critical('Can\'t find the kernel image! \n\n'
                         'Please use the --kernel-path option to specify '
                         'the path to the kernel image')
            exit(1)

        if args.initrd_path:
            log.debug(
                'Manually specified kernel path:\n ' +
                '                                %s' % args.initrd_path
            )
            initrd_path = args.initrd_path
        else:
            log.debug("No initrd specified, attempting automatic discovery")
            initrd_path = "/boot/%s-%s" % (opsys.initrd_name, opsys.kernel_release)

        if not os.path.exists(initrd_path):
            log.critical('Can\'t find the initrd image! \n\n'
                         'Please use the --initrd-path option to specify '
                         'the path to the initrd image')
            exit(1)

        # Check for kernel parameters. Without them, stop and fail
        if args.k_options:
            configuration['kernel_options'] = args.k_options
        else:
            try:
                configuration['kernel_options']
            except KeyError:
                error = ("cmdline was 'InvalidConfig'\n\n"
                         "Could not find any valid configuration. This "
                         "probably means that the configuration file is "
                         "corrupt. Either remove it to regenerate it from"
                         "default or fix the existing one.")
                log.critical(error)
                raise CmdLineError("No Kernel Parameters found")
                exit(2)

        log.debug(config.print_config())

        if args.setup_loader:
            configuration['setup_loader'] = args.setup_loader

        if args.install_stub:
            configuration['manage_mode'] = False

        if args.manage_mode:
            configuration['manage_mode'] = True

        force = False
        if args.force_update:
            force = True
        if configuration['force_update'] == True:
            force = True

        # Check our configuration to make sure it's good
        try:
            kernel_opts = configuration['kernel_options']
            esp_path = configuration['esp_path']
            setup_loader = configuration['setup_loader']
            manage_mode = configuration['manage_mode']
            force_update = configuration['force_update']

        except KeyError:
            log.critical(
                'Malformed configuration! \n'
                'The configuration we got is bad, and we can\'nt continue. '
                'Please check the config files and make sure they are correct. '
                'If you can\'t figure it out, then deleting them should fix '
                'the errors and cause kernelstub to regenerate them from '
                'Default. \n\n You can use "-vv" to get the configuration used.'
            )
            log.debug(
                'Configuration we got: \n\n%s' % config.print_config()
            )
            exit(4)

        drive = Drive.Drive(esp_path=esp_path)
        nvram = Nvram.NVRAM(opsys.name, opsys.version)
        installer = Installer.Installer(nvram, opsys, drive)

        # Make sure the destination exists on the ESP
        if not os.path.exists('%s%s' % (installer.work_dir,
                                        installer.os_dir_name)):
            os.makedirs('%s%s' % (installer.work_dir, installer.os_dir_name))

        # Log some helpful information, to file and optionally console
        info = (
            '    OS:..................%s %s\n'   %(opsys.name_pretty,opsys.version) +
            '    Drive name:........../dev/%s\n' % drive.name +
            '    Root partition:....../dev/%s\n' % drive.root_fs +
            '    Root FS UUID:........%s\n'      % drive.root_uuid +
            '    ESP Path:............%s\n'      % esp_path +
            '    ESP Partition:......./dev/%s\n' % drive.esp_fs +
            '    ESP Partition #:.....%s\n'      % drive.esp_num +
            '    NVRAM entry #:.......%s\n'      % nvram.os_entry_index +
            '    Boot Variable #:.....%s\n'      % nvram.order_num +
            '    Kernel Boot Options:.%s\n'      % kernel_opts +
            '    Kernel Image Path:...%s\n'      % kernel_path +
            '    Initrd Image Path:...%s\n'      % initrd_path
        )

        log.info('System information: \n\n%s' % info)
        log.debug('Setting up boot...')

        installer.backup_old(simulate=no_run)
        installer.setup_kernel(simulate=no_run)

        kopts = 'root=UUID=%s ro %s' % (drive.root_uuid, kernel_opts)

        if setup_loader:
            kopts = 'root=UUID=%s ro %s' % (drive.root_uuid, kernel_opts)
            installer.setup_loader(kopts, overwrite=force, simulate=no_run)

        if not manage_mode:
            kopts = 'root=UUID=%s ro %s' % (drive.root_uuid, kernel_opts)
            log.debug('kopts: %s' % kopts)
            installer.setup_stub(kopts, simulate=no_run)

        installer.copy_cmdline(simulate=no_run)



        config.config['user'] = configuration
        config.save_config()

        return 0

