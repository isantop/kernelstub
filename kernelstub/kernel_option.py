#!/usr/bin/python3

try:
    from debian.changelog import Version
    def vCompare(version1:str, version2:str):
        if Version(version1) > Version(version2):
            return True
        return False
        
except ImportError:
    from rpm import versionCompare as Version
    def vCompare(version1:str, version2:str):
        if versionCompare(version1, version2) == 1:
            return True
        return False
import os
import os.path

def options(path):
    items={}
    for name in os.listdir(path):
        key = None
        if name.startswith("vmlinuz-"):
            key = "kernel"
        elif name.startswith("initrd.img-"):
            key = "initrd"
        elif name.startswith("initramfs"):
            key = "initrd"

        if key is None:
            continue

        parts = name.split("-", 1)
        version = parts[1]

        if not version in items:
            items[version] = {}

        items[version][key] = os.path.join(path, name)

    return items

def get_newest_option(opts):
    latest_version = None
    latest_option = None

    for version, option in opts.items():
        # If option is not complete, skip
        if 'kernel' not in option or 'initrd' not in option:
            continue

        # If this option is newer, store this option and continue
        if latest_version is None or vCompare (version, latest_version):
            latest_version = version
            latest_option = option
    
    return latest_option, latest_version

def latest_option(path):
    opts = options(path)
    latest_option, latest_version = get_newest_option(opts)
    
    if latest_version is not None:
        opts.pop(latest_version)
    previous_option = None
    if len(opts) > 0:
        previous_option, latest_version = get_newest_option(opts)

    return latest_option, previous_option

if __name__ == "__main__":
    print(latest_option("/boot"))
