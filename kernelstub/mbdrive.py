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

import os
import logging
import subprocess

from . import util

class DriveError(Exception):
    """Exception used for drive errors. Pass details of the error in msg.

    Attributes: 
        msg (str): Human-readable message describing the error that threw the 
            exception.
        code (:obj:`int`, optional, default=4): Exception error code.
    
    Arguments:
        msg (str): Human-readable message describing the error that threw the 
            exception.
        code (int): Exception error code.
    """
    def __init__(self, msg, code=5):
        self.msg = msg
        self.code = code

class Drive():
    """
    Kernelstub Drive Object

    Stores and retrieves information related to the current drive.
    """

    def __init__(self, node=None, mount_point=None):

        self.log = logging.getLogger('kernelstub.Drive')
        self.log.debug('loaded kernelstub.Drive')

        if node: 
            self.node = node

        if mount_point:
            self.mount_point = mount_point
            try:
                self.node = self.equate_node_mountpoint(mount_point)[0]
            except DriveError:
                self.node = node
    
    @property
    def mtab(self):
        """:obj`dict`: A list of partitions on the system."""
        mtab = util.get_drives()
        return mtab

    @property
    def node(self):
        """str: the path to this partitions device node."""
        try:
            return self._node
        except AttributeError:
            return None
    
    @node.setter
    def node(self, node_path):
        """Try to set the node automatically by the mount-point, if mounted."""
        if node_path:
            # try:
            #     node_path = os.path.realpath(node_path)
            # except OSError:
            #     pass
            self._node = node_path
        else:
            raise DriveError(f'Could not set the node {node_path}')
    
    @property
    def mount_point(self):
        """str: the mount point for the partition."""
        try:
            return self._mount_point
        except AttributeError:
            return None
    
    @mount_point.setter
    def mount_point(self, mount_point):
        if mount_point:
            self._mount_point = mount_point
        else:
            raise DriveError(f'Could not set the mount point {mount_point}')
    
    @property
    def uuid(self):
        """str: The UUID for this partition in whatever format it supports."""
        self.log.debug('Looking for UUID for path %s' % self.node)
        try:
            result = subprocess.run(
                ['lsblk', '-f', '-o', 'NAME,UUID'],
                stdout=subprocess.PIPE
            )
            fs_list = result.stdout.decode('UTF-8').split('\n')
            self.log.debug(fs_list)
            for fs in fs_list:
                if os.path.basename(self.node) in fs:
                    uuid = fs.split()[-1]
                    return uuid
        except OSError as e:
            raise DriveError(f'Could not find the UUID for {self.node}') from e
    
    @property
    def drive_name(self):
        """str: The device node for the drive device this partitions is on."""
        # Ported from bash, out of @jackpot51's firmware updater
        efi_name = os.path.basename(os.path.realpath(self.node))
        efi_sys = os.readlink('/sys/class/block/{}'.format(efi_name))
        disk_sys = os.path.dirname(efi_sys)

        # We have a virtual mapper device, return dm-#.
        if "virtual" in disk_sys:
            return os.path.basename(efi_sys)

        # Otherwise, return the device node for the disk.
        disk_name = os.path.basename(disk_sys)
        self.log.debug('ESP is a partition on /dev/%s', disk_name)
        return disk_name
    
    @property
    def is_mounted(self):
        """bool: Whether the partition is mounted."""
        if self.node in self.mtab:
            return True
        return False
            
    def equate_node_mountpoint(self, part):
        """Try to match a device node with a mountpoint, or vice versa.

        Returns: 
            :obj:`tuple` of str: the node, the mountpoint
        """
        for mount in self.mtab:
            for key in self.mtab[mount]:
                if self.mtab[mount][key] == part:
                    return (self.mtab[mount]['node'], self.mtab[mount]['mount_point'])
        
        raise DriveError(
            f'Could not match {part} with any known mount-point or node.'
        )
    
    def mount_drive(self, mount_point=None, node=None, type=None):
        """ Mounts the drive into the system.

        This function does not check if a given drive is already present within 
        the system, so this type of checking should be performed first.

        Arguments:
            mount_point: str (optional): The mount point to place the filesystem
                at. If supplied, set the object's mount_point attribute to this.
                Otherwise, use the main mount_point attribute.
            node: str (optional): The device node to use. Uses the node 
                attribute by default.
            type: str (optional): The type of filesystem. Auto-detects if blank.
        """
        
        if not node:
            node = self.node
        if not mount_point:
            mount_point = self.mount_point
        if mount_point:
            self.mount_point = mount_point
        mount_cmd = ['sudo','mount']
        
        if type:
            mount_cmd += [f'-t {type}']
        
        mount_cmd += [node, mount_point]
        result = subprocess.run(mount_cmd, capture_output=True)
        if not result.returncode == 0:
            raise DriveError(
                f'Could not nmount the drive {self.node}:\n'
                f'{result.stderr.decode("UTF-8")}'
                f'mount return code: {result.returncode}'
            )

    def unmount_drive(self, drive=None):
        """ Unmounts the drive from the system.

        Arguments:
            drive: str(optional): The devices node or mountpoint to unmount. If
                blank, use the main node attribute.
        """

        if not drive:
            drive = self.node

        umount_cmd = ['sudo', 'umount', drive]
        result = subprocess.run(umount_cmd, capture_output=True)
        if not result.returncode == 0:
            raise DriveError(
                f'Could not unmount the drive {self.node}:\n'
                f'{result.stderr.decode("UTF-8")}'
                f'umount return code: {result.returncode}'
            )
