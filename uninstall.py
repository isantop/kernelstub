#!/usr/bin/python3

"""
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

 Removes kernelstub and its ESP and NVRAM entries
"""

import os, subprocess
import logging
import lsb_release

def run_command(command, simulate):
    logging.debug("Running command: "  + command)
    if simulate == True:
        output = "Simulating: " + command
        return output
    else:
        return subprocess.getoutput(command)

def get_os_name(lsbDict): # Get the name of the current OS, eg 'Ubuntu', or None
    osName = lsbDict.get('ID', None)
    return osName

def get_os_version(lsbDict): # Get the version number, eg '16.10', or None
    osVersion = lsbDict.get('RELEASE', None)
    return osVersion

def find_os_entry(nvram, osLabel):
    findIndex = 0
    for i in nvram:
            if osLabel in i:
                    logging.info("Found OS Entry")
                    logging.info("OS Entry is:       " + nvram[findIndex])
                    return findIndex
            else:
                    findIndex = findIndex + 1
    return -1

def del_boot_entry(index, sim): # Delete an entry from the NVRAM
    command = "efibootmgr -B -b " + index
    return run_command(command, sim)

def get_file_path(search): # Get path to file string, for copying stuff
    command = "ls /boot/" + search + "* | tail -1"
    return run_command(command, False)

def copy_files(src, dest, simulate): # Copy file src into dest
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

def check_config(path): # check if the config file exists
    if os.path.isfile(path) == True:
        f = open(path, "r")
        opts = f.readline()
        f.close()
        return opts
    else:
        return "InvalidConfig"

def main():
    
    logging.basicConfig(level=logging.DEBUG)
    
    # OS information (from LSB)
    lsbDict = lsb_release.get_distro_information()
    osName = get_os_name(lsbDict)
    osVer = get_os_version(lsbDict)
    osLabel = osName + " " + osVer
    
    # NVRAM information
    nvram = run_command("efibootmgr", False).split("\n")
    entryIndex = find_os_entry(nvram, osLabel)
    orderNum = str(nvram[entryIndex])[4:8]
    
    # Directory Information
    osDirName = osName + "-kernelstub/"
    workDir = "/boot/efi/EFI/" + osDirName
    linuxPath = get_file_path("vmlinuz")
    linuxName = "LINUX64.efi"
    linuxDest = workDir + linuxName
    initrdPath = get_file_path("initrd.img")
    initrdName = "initrd.img"
    initrdDest = workDir + initrdName
    cmdDest = workDir + "cmdline.txt"
    
    if entryIndex >= 0:
        logging.info("Deleting old boot entry")
        logging.info("New NVRAM:\n\n" + del_boot_entry(orderNum, False) + "\n")
    else:
        logging.info("No old entry to remove, skipping.")
    os.remove(initrdDest)
    os.remove(linuxDest)
    os.remove(cmdDest)
    os.remove("/etc/kernel/postinst.d/zz-kernelstub")
    os.remove("/etc/initramfs/postupdate.d/zz-kernelstub")
    
    return 0

if __name__ == '__main__':
    main()
