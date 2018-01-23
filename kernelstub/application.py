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

import logging, subprocess, shutil, os

from . import drive, nvram, opers

class CmdLineError(Exception):
    pass

class Kernelstub():

    def main(self, args): # Do the thing

        # Set up logging
        file_level = "INFO"
        verb = args.verbose
        if verb > 2:
            verb = 2

        verbosity = { None : "WARNING",
                      1 : "INFO",
                      2 : "DEBUG" }

        console_level = verbosity[verb]

        if args.log:
                log_file = args.log
        else:
            log_file = "/var/log/kernelstub.log"
        logging.basicConfig(level = file_level,
                            format = ('%(asctime)s %(name)-12s '
                                      '"%(levelname)-8s %(message)s'),
                            datefmt = '%m-%d %H:%M',
                            filename = log_file,
                            filemode = 'w')
        console = logging.StreamHandler()
        console.setLevel(console_level)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        # Figure out runtime options
        if args.simulate:
            noRun = True
        else:
            noRun = False

        if args.kernelpath:
            linux_path = args.kernelpath
        else:
            logging.info("No kernel specified, attempting automatic discovery")
            linux_path = self.get_file_path("/boot/", "vmlinuz")

        if args.initrd_path:
            initrd_path = args.initrd_path
        else:
            logging.info("No initrd specified, attempting automatic discovery")
            initrd_path = self.get_file_path("/boot/", "initrd.img")

        # First check for kernel parameters. Without them, stop and fail
        if not args.cmdline:
            config_path = "/etc/default/kernelstub"
            try:
                kernel_opts = self.check_config(config_path)
            except:
                error = ("cmdline was 'InvalidConfig'\n\n"
                         "This probably means that the config file doesn't exist "
                         "and you didn't specify any boot options on the command "
                         "line.\n"
                         "Create a new config file in /etc/default/kernelstub with "
                         "your required kernel parameters and rerun kernelstub "
                         "again!\n\n")
                logging.critical(error)
                raise CmdLineError("No Kernel Parameters found")
                return 3
        else:
            kernelOpts = args.cmdline

        # Get the objects
        this_os = opers.OS()
        this_drive = drive.Drive()
        this_nvram = nvram.NVRAM(this_os.os_name, this_os.os_version)

        # Directory Information
        os_dir_name = this_os.os_name + "-kernelstub/"
        work_dir = "/boot/efi/EFI/" + os_dir_name
        linux_name = "linux64.efi"
        linux_dest = work_dir + linux_name
        initrd_name = "initrd.img"
        initrd_dest = work_dir + initrd_name

        self.ensure_dir(work_dir) # Make sure the destination exists on the ESP

        # Log some helpful information, to file and optionally console
        logging.info("NVRAM entry index: %s" % str(this_nvram.os_entry_index))
        logging.info("Boot Number:       %s" % this_nvram.order_num)
        logging.info("Drive name is      %s" % this_drive.drive_name)
        logging.info("Root FS is on      %s" % this_drive.root_fs)
        logging.info("ESP data is on     %s" % this_drive.esp_fs)
        logging.info("ESP partition #:   %s" % this_drive.esp_num)
        logging.info("Root FS UUID is:   %s" % this_drive.root_uuid)
        logging.info("OS running is:     %s %s" % (this_os.os_name, this_os.os_version))
        logging.info("Kernel Params:     %s" % kernel_opts)

        # Do stuff
        logging.info("Now running the commands\n")
        try:
            self.copy_files(linux_path, linux_dest, noRun)
        except FileOpsError:
            error = ("Could not copy the Kernel Image  into the ESP! This "
                     "indicates a very bad problem and it is unsafe to continue. "
                     "Aborting now...")
            logging.critical(error)
            return 2

        try:
            self.copy_files(initrd_path, initrd_dest, noRun)
        except FileOpsError:
            error = ("Could not copy the initrd.img  into the ESP! This indicates "
                     "a very bad problem and it is unsafe to continue. Aborting "
                     "now...")
            logging.critical(error)
            return 3

        # Check for an existing NVRAM entry and remove it if present
        if this_nvram.os_entry_index >= 0:
            logging.info("Deleting old boot entry")
            this_nvram.delete_boot_entry(this_nvram.os_entry_index)
            logging.info('New NVRAM: \n\n%s\n' % this_nvram.nvram)
        else:
            logging.info("No old entry to remove, skipping.")
        this_nvram.add_entry(this_os, this_drive, kernel_opts)
        logging.info('New NVRAM:\n\n%s\n' % this_nvram.nvram)

        try:
            self.copy_files("/proc/cmdline", work_dir + "cmdline.txt", noRun)
        except FileOpsError:
            error = ("Could not copy the current Kernel Command line into the ESP. "
                     "You should manually copy the contents of /proc/cmdline into "
                     "the ESP to ensure you can get to it in an emergency. This is "
                     "a non-critical error, so continuing without it.")
            logging.warning(error)
            pass
        return 0

    def get_file_path(self, path, search): # Get path to file string, for copying stuff
        command = "ls " + path + search + "* | tail -1"
        return subprocess.getoutput(command)

    def copy_files(self, src, dest, simulate): # Copy file src into dest
        if simulate == True:
            copy = ("Simulate copying " + src + " into " + dest)
            logging.info(copy)
            return True
        else:
            copy = ("Copying " + src + " into " + dest)
            logging.info(copy)
            try:
                shutil.copy(src, dest)
                return True
            except:
                logging.error("Copy failed! Things may not work...")
                raise FileOpsError("Could not copy one or more files.")
                return False

    def ensure_dir(self, file_path): # Make sure a file exists, and make it if it doesn't
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def check_config(self, path): # check if the config file exists, read it
        if os.path.isfile(path) == True:
            f = open(path, "r")
            opts = f.readline()
            f.close()
            return opts
        else:
            raise ConfigError("Missing configuration, cannot continue")
            return "InvalidConfig"
