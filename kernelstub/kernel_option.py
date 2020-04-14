#!/usr/bin/python3

from debian.changelog import Version
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
        if latest_version is None or Version(version) > Version(latest_version):
            latest_version = version
            latest_option = option
    
    return latest_option, latest_version

def latest_option(path):
    opts = options(path)
    latest_option, latest_version = get_newest_option(opts)
    
    opts.pop(latest_version)
    previous_option = None
    if len(opts) > 0:
        previous_option, latest_version = get_newest_option(opts)

    return latest_option, previous_option

if __name__ == "__main__":
    print(latest_option("/boot"))
