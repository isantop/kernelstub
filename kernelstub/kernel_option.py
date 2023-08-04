#!/usr/bin/python3

import logging

log = logging.getLogger('kernelstub.kernel_option')

try:
    from debian.changelog import Version
    def vCompare(version1:str, version2:str):
        if Version(version1) > Version(version2):
            return True
        return False
        
except ImportError:
    from rpm import labelCompare
    def vCompare(version1:str, version2:str):
        if labelCompare(version1, version2) == 1:
            return True
        return False
import os
import os.path

def options(path):
    items={}
    for name in os.listdir(path):
        log.info('Checking item %s', name)
        key = None
        if name.startswith("vmlinuz-"):
            log.info('Item %s is kernel-image', name)
            key = "kernel"
        elif name.startswith("initrd.img-"):
            log.info('Item %s is debian-style initrd', name)
            key = "initrd"
        elif name.startswith("initramfs"):
            log.info('Item %s is fedora-style initrd', name)
            key = "initrd"

        if key is None:
            continue

        parts = name.split("-", 1)
        version = parts[1]
        if version.endswith('.img'):
            version = version[:-4]
        log.info('Item version is %s', version)

        if not version in items:
            log.info('Adding item %s to list', name)
            items[version] = {}

        items[version][key] = os.path.join(path, name)

    log.info('Found items: %s', items)
    return items

def get_newest_option(opts):
    log.info('Getting latest boot item version')
    latest_version = None
    latest_option = None

    for version, option in opts.items():
        log.info('Checking option %s', option)
        # If option is not complete, skip
        if 'kernel' not in option or 'initrd' not in option:
            log.info('%s does not contain all items, skipping...', version)
            continue

        # If this option is newer, store this option and continue
        if latest_version is None or vCompare (version, latest_version):
            log.info('%s is the latest version', version)
            latest_version = version
            latest_option = option
    
    return latest_option, latest_version

def latest_option(path):
    log.info('Checking for boot items in %s', path)
    opts = options(path)
    latest_option, latest_version = get_newest_option(opts)
    
    if latest_version is not None:
        opts.pop(latest_version)
    previous_option = None
    if len(opts) > 0:
        previous_option, latest_version = get_newest_option(opts)

    log.info('Latest option: %s', latest_option)
    log.info('Previous option: %s', previous_option)
    return latest_option, previous_option

if __name__ == "__main__":
    print(latest_option("/boot"))
