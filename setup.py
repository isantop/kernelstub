#!/usr/bin/python3

"""
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

Portions of test-related code authored by Jason DeRose <jason@system76.com>
"""


from setuptools import setup
from distutils.cmd import Command
import os
import subprocess
import sys

TREE = os.path.dirname(os.path.abspath(__file__))
DIRS = [
    'kernelstub',
    'bin'
]

def run_pytest():
    return run_under_same_interpreter('test', '/usr/bin/pytest-3', [])

def run_under_same_interpreter(opname, script, args):
    """Re-run with the same as current interpreter."""
    print('\n** running: {}...'.format(script), file=sys.stderr)
    if not os.access(script, os.R_OK | os.X_OK):
        print(
            'ERROR: cannot read and execute: {!r}'.format(script),
            file=sys.stderr
        )
        print(
            'Consider running `setup.py test --skip-{}`'.format(opname),
            file=sys.stderr
        )
        sys.exit(3)
    cmd = [sys.executable, script] + args
    print('check_call:', cmd, file=sys.stderr)
    try:
        subprocess.check_call(cmd)
        print('** PASSED: {}\n'.format(script), file=sys.stderr)
        return True
    except subprocess.CalledProcessError:
        print('** FAILED: {}\n'.format(script), file=sys.stderr)
        return False

def run_pyflakes3():
    """Run a round of pyflakes3."""
    script = '/usr/bin/pyflakes3'
    names = [
        'setup.py',
    ] + DIRS
    args = [os.path.join(TREE, name) for name in names]
    return run_under_same_interpreter('flakes', script, args)



class Test(Command):
    """Basic sanity checks on our code."""
    description = 'run pyflakes3'

    user_options = [
        ('skip-flakes', None, 'do not run pyflakes static checks'),
        ('skip-test', None, 'Do run run unit tests')
    ]

    def initialize_options(self):
        self.skip_sphinx = 0
        self.skip_flakes = 0
        self.skip_test = 0

    def finalize_options(self):
        pass

    def run(self):
        if not self.skip_flakes:
            pf3 = run_pyflakes3()
        if not self.skip_test:
            pt3 = run_pytest()
        if not pt3 or not pf3:
            print(
                'ERROR: One or more tests failed with errors.'
            )
            exit(3)

setup(
    name='kernelstub',
    version='4.0.0',
    author='Ian Santopietro',
    author_email='isantop@gmail.com',
    url='https://launchpad.net/kernelstub',
    description='Automatic kernel efistub manager for UEFI',
    download_url='https://launchpad.net/kernelstub/releases',
    tests_require=['pytest'],
    license='ISC',
    packages=['kernelstub'],
    scripts=['bin/kernelstub'],
    cmdclass={'test': Test},
    data_files=[
        ('/etc/kernel/postinst.d', ['data/kernel/zz-kernelstub']),
        ('/etc/initramfs/post-update.d', ['data/initramfs/zz-kernelstub']),
        ('/etc/default', ['data/config/kernelstub.SAMPLE'])
    ]
)
