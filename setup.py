#!/usr/bin/python3

"""
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
"""


from distutils.core import setup

setup(name='kernelstub',
    version='1.0.0',
    description='Automatic kernel efistub manager for UEFI',
    url='https://launchpad.net/kernelstub',
    author='Ian Santopietro',
    author_email='isantop@gmail.com',
    license='BSD',
    packages=['kernelstub'],
    scripts=['kernelstub/kernelstub'],
    data_files=[
        ('/etc/kernel/postinst.d', ['kernelstub/data/kernel/zz-kernelstub']),
        ('/etc/initramfs/post-update.d', ['kernelstub/data/initramfs/zz-kernelstub']),
        ('/etc/default', ['kernelstub/data/kernelstub']),
        ('/usr/bin', ['kernelstub/kernelstub']),
        ('/usr/share/man/man1'), ['kernelstub/data/kernelstub.1.gz']),
        ('/usr/share/man/man1'), ['kernelstub/data/kernelstub_config.5.gz'])]
    )
