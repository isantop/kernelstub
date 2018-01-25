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

from . import drive as idrive
from . import nvram as invram
from . import opsys as iopsys
from . import installer as iinstaller
from . import config as iconfig

class CmdLineError(Exception):
    pass

class Kernelstub():

    def main(self, args): # Do the thing

        file_level = 'INFO'
        verbosity = args.verbose
        if verbosity == None:
            verbosity = 0
        if verbosity > 2:
            verbosity = 2

        level = {
            0 : 'WARNING',
            1 : 'INFO',
            2 : 'DEBUG',
        }

        console_level = level[verbosity]

        if args.log:
                log_file = args.log
        else:
            log_file = "/var/log/kernelstub.log"

        log = logging.getLogger('kernelstub')
        console = logging.StreamHandler()
        stream_fmt = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(stream_fmt)
        log.addHandler(console)
        log.setLevel(console_level)
        log.debug('Logging set up')

        # Figure out runtime options
        if args.simulate:
            no_run = True
        else:
            no_run = False

        config = iconfig.Config()
        whole_config = config.load_config()
        try:
            if whole_config['user']:
                configuration = whole_config['user']
        except KeyError:
            whole_config['user'] = whole_config['default']
            configuration = whole_config['user']

        manage = False
        if args.manage:
            manage = True
            configuration['manage_mode'] = manage
        if configuration['manage_mode'] == True:
            manage = True

        force = False
        if args.force:
            force = True
        if configuration['force_update'] == True:
            force = True

        # First check for kernel parameters. Without them, stop and fail
        if not args.cmdline:
            config_path = "/etc/default/kernelstub"
            try:
                kernel_opts = configuration['kernel_options']
            except:
                error = ("cmdline was 'InvalidConfig'\n\n"
                         "This probably means that the config file doesn't exist "
                         "and you didn't specify any boot options on the command "
                         "line.\n"
                         "Create a new config file in /etc/default/kernelstub with "
                         "your required kernel parameters and rerun kernelstub "
                         "again!\n\n")
                log.critical(error)
                raise CmdLineError("No Kernel Parameters found")
                return 3
        else:
            kernel_opts = args.cmdline
            configuration['kernel_options'] = kernel_opts

        opsys = iopsys.OS()

        if args.kernelpath:
            linux_path = args.kernelpath
        else:
            log.info("No kernel specified, attempting automatic discovery")
            linux_path = "/boot/%s-%s" % (opsys.kernel_name, opsys.kernel_release)

        if args.initrd_path:
            initrd_path = args.initrd_path
        else:
            log.info("No initrd specified, attempting automatic discovery")
            initrd_path = "/boot/%s-%s" % (opsys.initrd_name, opsys.kernel_release)

        drive = idrive.Drive()
        nvram = invram.NVRAM(opsys.name, opsys.version)
        installer = iinstaller.Installer(nvram, opsys, drive)

        # Make sure the destination exists on the ESP
        if not os.path.exists('%s%s' % (installer.work_dir,
                                        installer.os_dir_name)):
            os.makedirs('%s%s' % (installer.work_dir, installer.os_dir_name))

        # Log some helpful information, to file and optionally console
        log.info("NVRAM entry index:  %s" % nvram.os_entry_index)
        log.info("Boot Number:        %s" % nvram.order_num)
        log.info("Drive name is       %s" % drive.drive_name)
        log.info("Root FS is on       %s" % drive.root_fs)
        log.info("ESP data is on      %s" % drive.esp_fs)
        log.info("ESP partition #:    %s" % drive.esp_num)
        log.info("Root FS UUID is:    %s" % drive.root_uuid)
        log.info("OS running is:      %s %s" % (opsys.name, opsys.version))
        log.info("Kernel Params:      %s" % kernel_opts)
        log.info("Kernel image path:  %s" % linux_path)
        log.info("Ramdisk image path: %s" % initrd_path)

        log.debug('Setting up boot...')

        installer.backup_old(simulate=no_run)
        installer.setup_kernel(simulate=no_run)

        if manage:
            kopts = 'root=UUID=%s ro %s' % (drive.root_uuid, kernel_opts)
            installer.setup_loader(kopts, overwrite=force)
        else:
            kopts = 'root=UUID=%s ro %s' % (drive.root_uuid, kernel_opts)
            log.debug('kopts: %s' % kopts)
            installer.setup_stub(kopts, simulate=no_run)

        installer.copy_cmdline(simulate=no_run)

        whole_config['user'] = configuration
        config.save_config(whole_config)

        return 0

    def check_config(self, path): # check if the config file exists, read it
        opts = []
        if os.path.isfile(path) == True:
            with open(path, "r") as config_file:
                opts = config_file.readlines()
            return opts[0]
        else:
            raise ConfigError("Missing configuration, cannot continue")
            return "InvalidConfig"
