 kernelstub Version 0.2

 The automatic manager for using the Linux Kernel EFI Stub to boot
 
 Copyright 2017 Ian Santopietro <isantop@gmail.com>

 Redistribution and use in source and binary forms, with or without 
 modification, are permitted provided that the following conditions are met:

 1. Redistributions of source code must retain the above copyright notice, this 
 list of conditions and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright notice, 
 this list of conditions and the following disclaimer in the documentation and/
 or other materials provided with the distribution.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
 AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
 ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
 LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
 CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
 SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
 INTERRUPTION) HOWEVER  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
 CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
 ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
 POSSIBILITY OF SUCH DAMAGE.

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
 
INSTALLATION
 Installation is simple, and only requires running the install.sh shell script.
 This will prompt you for sudo privileges if required, then install the relevant
 portions of the program in their correct places, including an automatic trigger
 to run during kernel updates. The install scripts will NOT install a 
 configuration file; for details, see the CONFIGURATION section.
 
USAGE
 Usage is straightforward, and typically only requires running the program as
 root (or with sudo/su). A full explanation of available options is below:
 
 usage: kernelstub [-h] [-k KERNELOPTS] [-l LOG] [-lv LOG_LEVEL] [-v] [-s]

 optional arguments:
   -h, --help            show this help message and exit
   -k KERNELOPTS, --kernelopts KERNELOPTS
                         Specify the kernel boot options to use (eg. ro quiet
                         splash). Default is to read from the config file in
                         /etc/default/kernelstub. Options MUST be specified
                         either in the config file or using this option,
                         otherwise no action will be taken!
   -l LOG, --log LOG     Path to the log file. Default is
                         /var/log/kernelstub.log
   -lv LOG_LEVEL, --log-level LOG_LEVEL
                         Sets the information level for the log file. Default
                         is INFO. Valid options are DEBUG, INFO, WARNING,
                         ERROR, and CRITICAL.
   -v, --verbose         Displays extra information about the actions being
                         performed.
   -s, --simulate        Don't actually run any commands, just simulate them.
                         This is useful for testing.
 
 By default, kernelstub will display no output and return with exit status 0. 
 You can enable additional output by passing the -v flag. You can also check
 the log file, which is located in /var/log/kernelstub by default. An alternate
 location can be given by passing the -l argument. 
 
CONFIGURATION
 Kernelstub will attempt to automatically configure as many items as possible, 
 given a set of sane defaults. It will use UUID to identify the root partition 
 to the kernel, and uses full device names wherever possible. The only 
 configuration availble is for kernel options, which MUST be given for the 
 program to function properly; failure to provide kernel options will result in
 an error code. 
 
 Kernel parameters can be supplied through the /etc/default/kernelstub file, and
 this is recommended since it will enable automatic handling of kernel updates. 
 If you wish, you can also specify parameters using the -k or --kernelopts 
 flags. Please note that these are not automatically stored in the config file, 
 so work better for single-kernel boot overrides.
 
 The /etc/default/kernelstub config file is NOT provided by default, however a 
 sample file is located at /etc/default/kernelstub.SAMPLE. Only the first line 
 of the file is read, so you must place the kernel parameters here. Other lines 
 in the file are ignored. 
 
 If you're unsure what kernel parameters you will need, you can get the ones 
 used in the current boot by looking at /proc/cmdline. However, please be aware 
 that kernelstub will supply the boot-image, root, initrd, and ro options 
 automatically, so you only need to include any other options. Generally these 
 include "quiet splash" or other compatibility tweaks like "nomodeset". You can 
 also find the parameters in the /etc/default/grub file, in the GRUB_CMDLINE_
 LINUX_DEFAULT and GRUB_CMDLINE_LINUX options. 
