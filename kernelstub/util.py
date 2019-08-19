#!/usr/bin/python3

"""
 kernelstub
 Comprehensive automatic ESP Management for Linux.

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

This is a utility module for kernelstub which contains several package-wide 
functions which are useful to these 

Attributes:
    SYSTEMD_SUPPORT (bool): Whether the system supports systemd for logging.

TODO:
"""

import argparse
import logging
from logging import handlers
import platform
import sys

# Try detecting systemd support
SYSTEMD_SUPPORT = False
try:
    from systemd.journal import JournalHandler
    SYSTEMD_SUPPORT = True

except ImportError:
    pass

def get_os_release():
    """Get information about the current OS from /etc/os-release.
    
    Returns:
        A :list: with the information contained.
    """
    try:
        with open('/etc/os-release') as os_release_file:
            os_release = os_release_file.readlines()
    except FileNotFoundError:
        pass

    return os_release

def get_os_name():
    """Get the name of the currently running OS.
    
    Returns:
        A :str: containing the official name of the OS.
    """
    os_release = get_os_release()
    for item in os_release:
        if item.startswith('NAME='):
            name = item.split('=')[1]
            return strip_quotes(name[:-1])

def get_os_version():
    """Get the current OS version number
    
    Returns:
        A :str: with the current OS official version number.
    """
    os_release = get_os_release()
    for item in os_release:
        if item.startswith('VERSION_ID='):
            version = item.split('=')[1]
            return strip_quotes(version[:-1])

def get_hostname():
        """Get the current system hostname.
        
        Returns:
            The :obj:`str` of the current hostname
        """
        return platform.node()

def clean_names(name):
    """Removes bad characters from names.

    This is a list of characters we can't/don't want to have in technical
    names for the OS. name_pretty will still have them.

    Arguments:
        name (str): The name to strip bad characters from.
    
    Returns:
        An :obj:`str` without any of the bad characters.
    """
    badchar = {
        ' ' : '_',
        '~' : '-',
        '!' : '',
        "'" : "",
        '<' : '',
        '>' : '',
        ':' : '',
        '"' : '',
        '/' : '',
        '\\' : '',
        '|' : '',
        '?' : '',
        '*' : '',
        '(' : '',
        ')' : '',
        'CON' : '',
        'PRN' : '',
        'AUX' : '',
        'NUL' : '',
        'COM1' : '',
        'COM2' : '',
        'COM3' : '',
        'COM4' : '',
        'COM5' : '',
        'COM6' : '',
        'COM7' : '',
        'COM8' : '',
        'COM9' : '',
        'LPT1' : '',
        'LPT2' : '',
        'LPT3' : '',
        'LPT4' : '',
        'LPT5' : '',
        'LPT6' : '',
        'LPT7' : '',
        'LPT8' : '',
        'LPT9' : '',
    }

    for char in badchar:
        name = name.replace(char, badchar[char])
    return name

def strip_quotes(value):
    """Strip quotes from a value.

    Only removes leading or trailing quotation marks.
    
    Arguments:
        value (str): The value from which to strip quotes.

    Returns:
        The :obj:`str` without quotation marks.
    """
    new_value = value
    if value.startswith('"') or value.startswith("'"):
        new_value = new_value[1:]
    if value.endswith('"') or value.endswith("'"):
        new_value = new_value[:-1]
    return new_value

def get_drives():
    """Get the current system mtab.
    
    The mtab is the table of mounted block devices.

    Returns:
        An :obj:`dict` containing the mtab

    """
    with open('/proc/mounts') as proc_mounts:
        mtab_list = proc_mounts.readlines()

    mtab = {}
    for partition in mtab_list:
        unparsed = partition.split()
        parsed = {}
        parsed['node'] = unparsed[0]
        parsed['mount_point'] = unparsed[1]
        parsed['type'] = unparsed[2]
        parsed['options'] = unparsed[3]
        mtab[unparsed[0]] = parsed
    return mtab

def parse_options(options):
    """
    Parse a list of kernel options

    Takes a list object and ensure that each item in the list is a single
    linux kernel option. Returns the resulting list.

    Args:
        options (str): The string of kernel options.
    
    Returns:
        a :obj:`list` with each option as a :obj:`str`.

    """
    buff = ''
    quote = False
    options = []
    for ch in optstr:
        if not quote:
            if not ch is " ":
                buff += ch
                if ch is "'" or ch is '"':
                    quote = True
            elif not quote and ch is " ":
                options.append(buff)
                buff = ''
        elif quote: 
            buff += ch
            if ch is '"' or ch is "'":
                quote = False
                options.append(buff)
                buff = ''
    while('' in options):
        options.remove('')
    return options

def get_args(raw_args=None):
    """Set up command line argument parsing.

    Without options, use the argparse module default (sys.argv)
    
    Arguments:
        raw_args (list, optional): The list of arguments to send to the parser.
    
    Returns:
        An :obj:`Namespace` containing all of the arguments.
    """
    parser = argparse.ArgumentParser(
        description='Comprehensive ESP management for Linux.'
    )
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers()

    # Main System Arguments
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Make program output more verbose.'
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='Supress program output.'
    )
    parser.add_argument(
        '-c',
        '--config',
        help='Path to configuration directory'
    )
    parser.add_argument( 
        '-l',
        '--loader',
        help=argparse.SUPPRESS # This option is not complete
    )
    parser.add_argument(
        '-g',
        '--log-file',
        help='Path to log file'
    )
    parser.add_argument(
        '--preserve-live-mode',
        action='store_true',
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        '--enable-live-mode',
        action='store_true',
        help=argparse.SUPPRESS
    )
    # parser.add_argument(
    #     'command',
    #     nargs='?',
    #     help='The subcommand to execute'
    # )

    # System Subcommand
    parser_system = subparsers.add_parser(
        'system',
        description='Modify System Configuration',
        help='Modify System Configuration'
    )
    parser_system.set_defaults(func="system")
    parser_system.add_argument(
        '-m',
        '--menu-timeout',
        metavar='S',
        help='Set the number of seconds the boot menu displays'
    )
    parser_system.add_argument(
        '-e',
        '--esp',
        metavar='PATH',
        help='Path to the EFI System Partition'
    )

    # Create Subcommand
    parser_create = subparsers.add_parser(
        'create',
        description='Creates a new entry and register it with the system.',
        help='Creates a new entry and register it with the system.'
    )
    parser_create.set_defaults(func="create")
    parser_create.add_argument(
        '-n',
        '--entry-id',
        help='The new entry ID for this entry.'
    )
    parser_create.add_argument(
        '-t',
        '--title',
        help='The title for this entry'
    )
    parser_create.add_argument(
        '-r',
        '--root',
        help='Device node for the root partition'
    )
    parser_create.add_argument(
        '-m',
        '--mount-point',
        help='Mount point for the root partition'
    )
    parser_create.add_argument(
        '-e',
        '--exec-path',
        help='Path to the EFI executable or kernel image'
    )
    parser_create.add_argument(
        '-i',
        '--initrd-path',
        help='Path to the initrd image (for linux entries)'
    )
    parser_create.add_argument(
        '-o',
        '--options',
        help='Linux Kernel command line options for this entry.'
    )
    parser_create.add_argument(
        '-x',
        '--index',
        help='An optional index for the new entry.'
    )
    parser_create.add_argument(
        '-s',
        '--set-default',
        action='store_true',
        help='Set this new entry as the default boot entry'
    )

    # List Subcommand
    parser_list = subparsers.add_parser(
        'list',
        description=(
            'List registered entries, and optionally list the present '
            'configuration for an entry'
        ),
        help=(
            'List registered entries, and optionally list the present '
            'configuration for an entry'
        )
    )
    parser_list.set_defaults(func="lst")
    parser_list.add_argument(
        'index',
        nargs='?',
        help='Which entry to list configuration for.'
    )

    # Update Subcommand
    parser_update = subparsers.add_parser(
        'update',
        description='Update one or all entries in the configuration',
        help='Update one or all entries in the configuration'
    )
    parser_update.set_defaults(func="update")
    parser_update.add_argument(
        'index',
        nargs='?',
        help='The entry index to update'
    )

    # Edit Subcommand
    parser_edit = subparsers.add_parser(
        'edit',
        description='Modify an entry\'s configuration',
        help='Modify an entry\'s configuration'
    )
    parser_edit.set_defaults(func="edit")
    parser_edit.add_argument(
        'index',
        help='The entry index to modify; use `list` for a list.'
    )
    parser_edit.add_argument(
        '-n',
        '--entry-id',
        help='The new entry ID for this entry.'
    )
    parser_edit.add_argument(
        '-t',
        '--title',
        help='The title for this entry'
    )
    parser_edit.add_argument(
        '-r',
        '--root',
        help='Device node for the root partition'
    )
    parser_edit.add_argument(
        '-m',
        '--mount-point',
        help='Mount point for the root partition'
    )
    parser_edit.add_argument(
        '-e',
        '--exec-path',
        help='Path to the EFI executable or kernel image'
    )
    parser_edit.add_argument(
        '-i',
        '--initrd-path',
        help='Path to the initrd image (for linux entries)'
    )
    parser_edit.add_argument(
        '-o',
        '--options',
        help='Linux Kernel command line options for this entry'
    )
    parser_edit.add_argument(
        '-a',
        '--add-options',
        help='Add new options without affecting existing options'
    )
    parser_edit.add_argument(
        '-d',
        '--delete-options',
        help='Remove select options without affecting other options'
    )
    parser_edit.add_argument(
        '-s',
        '--set-default',
        action='store_true',
        help='Set this new entry as the default boot entry'
    )

    # Delete Subcommand
    parser_delete = subparsers.add_parser(
        'delete',
        description='Delete an entry from the system',
        help='Delete an entry from the system'
    )
    parser_delete.set_defaults(func="delete")
    parser_delete.add_argument(
        'index',
        help='The entry index to delete; use `list` for a list.'
    )
    parser_delete.add_argument(
        '-r',
        '--retain-data',
        action='store_true',
        help=(
            'Keeps the entry bootloader on the ESP.'
        )
    )
    if raw_args:
        return parser.parse_args(raw_args)
    return parser.parse_args()

def setup_logging(verbosity, log_file_path):
    """Sets up a logger object to handle all of our logging.

    If the system supports logging to the systemd journal, the resulting 
    logger will log there as well as to the kernelstub log.
    
    Arguments:
        verbosity (int): The verbosity level from 0 to 2. Lower is less verbose.
        log_file_path (str): The path to the log file to store
    
    Returns:
        An :obj:`logging.Logger` with the specified parameters
    """
    level = {
        0 : logging.WARNING,
        1 : logging.INFO,
        2 : logging.DEBUG,
    }

    console_level = level[verbosity]
    file_level = level[2]

    stream_fmt = logging.Formatter(
        '%(levelname)s: %(message)s')
    file_fmt = logging.Formatter(
        '%(asctime)s - %(name)s: %(levelname)s: %(message)s')
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

    return log