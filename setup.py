#!/usr/bin/python3

from distutils.core import setup

setup(name='kernelstub',
    version='0.18',
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
        ('/etc/default', ['kernelstub/data/kernelstub.SAMPLE'])]
    )
