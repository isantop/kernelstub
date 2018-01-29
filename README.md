## Kernelstub

The automatic manager for booting Linux on (U)EFI.

Kernelstub is a utility to automatically manage your OS's EFI System Partition
(ESP). It makes it simple to copy the current kernel and initramfs image onto
the ESP so that they are automatically probable by most EFI boot loaders as well
as the EFI firmware itself. It can also set up the system's NVRAM to add entries
to the firmware boot menu for the kernel (and keep these options up to date when
new kernel versions are installed).

### Installation

Installation can be handled through the supplied Debian packaging as well as the
python packaging. If kernelstub is packaged in your distro's repositories, you
can install kernelstub through the `kernelstub` package. To build a debian
package locally, use these commands:
```
git clone https://github.com/isantop/kernelstub
cd kernelstub
debuild -B
sudo dpkg -i ../kernelstub*.deb
```
For installation on non-debian systems, or if you prefer to use Python
packaging, use:
```
git clone https://github.com/isantop/kernelstub
cd kernelstub
sudo python3 setup.py install --record > installed_files.txt
```
For your convenience, this will create a list of all files installed on the
system in the `installed_files.txt` file, so that you can easily remove the
package later.


### Usage

Usage is fairly straightforward and usually only requires running the command as
root with `su`/`sudo`. If your computer requires special kernel parameters to
boot, you can specify them as such:
```
sudo kernelstub -c "options_go here wrapped in-quotes"
```
Running the command with `-o` will save the options used into the user section
of the configuration file (see _Configuration_ below) so that you don't need to
specify them manually each time you run it.

Kernelstub assumes the `quiet splash` options by default, since these generally
work on every system, at least for booting up to a usable system.

You can get output of the program using the `-v`/`--verbose` option. There are
three levels of verbosity. The default is to only show `Warning`, `Error`, and
`Critical` failure messages. With one `-v`, kernelstub will display information
about its progress to the command line. Two `-v` flags will also display
debugging information generally only useful to developers.

By default, kernelstub will attempt to set up an entry in the system NVRAM to
boot the kernel directly. If you want to use kernelstub with a separate program
(e.g. `bootctl`/`systemd-boot` or rEFIt/rEFInd), you can use the `-m` flag. This
causes kernelstub to copy the kernel and initrd into the ESP, but not set up any
NVRAM entries. The `-l` option also explicitly sets up the configuration for
`system-boot` or `gummiboot`. These options are also stored in the config file.

There are other options as well, as detailed below:

| Option                   | Action                                            |
|--------------------------|---------------------------------------------------|
|`-h`, `--help`            | Display the help Text                             |
|`-d`, `--dry-run`         | Don't actually copy any files or set anything up. |
|`-e PATH`, `--esp_path`   | Manually specify the ESP path.*		       |
|`-k PATH`, `--kernelpath` | Manually specify the path to the kernel image.    |
|`-i PATH`, `--initrd_path`| Manually specify the path to the initrd image.    |
|`-o "options"`,`--options`| Set kernel boot options.*			       |
|`-l`, `--loader`          | Create a `systemd-boot`-compatible loader config.*|
|`-s`, `--stub`            | Set up NVRAM entries for the copied kernel.       |
|`-m`, `--manage-only`	   | Don't set up any NVRAM entries.*                  |
|`-f`, `--force-update`    | Forcefully update the main loader.conf.**         |
|`-v`, `--verbose`         | Display more information to the command line      |

*These options save information to the config file.
**This may overwrite another OS's information.

### Configuration

Kernelstub has a robust configuration system with multiple fallbacks for safety.
By default, a sample (non-functional) configuration file is provided in
`/etc/kernelstub/SAMPLE` which demonstrates the available options and
the JSON syntax. The main configuration file is stored in
`/etc/kernelstub/configuration`, which is created by default if it doesn't exist.
Kernelstub also has a copy of the default configuration stored internally, so
that it can create a config file if none already exists.

When kernelstub is run with the `-o`, `-l`, `-s`, or `-m` options, this is
recorded in the config file so that future automatic runs or runs without
options will work correctly. Options specified on the command line always take
precedence over options in the config files.

Your distribution or package maintainer may additionally create a configuration
template in `/etc/default/kernelstub`. This should not be edited except by
maintaners. Use the standard config file instead, as this will be loaded instead
of the distributor file if it exists, and options will never be saved to the
distributor file.


### Return codes

If kernelstub is going to be used in a scripted environment, it is useful to
know what return codes it provides in the event of errors. If everything
appeared to work correctly and kernelstub exited successfully, it returns 0. If
there was a problem parsing the configuration file, it returns 2. If there was a
problem copying a file needed for installation, it returns 3.


### Licence

Kernelstub is available under an ISC-based licence. The full licence is below:

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

