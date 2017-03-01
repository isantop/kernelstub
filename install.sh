#!/bin/bash

# Install kernelstub
sudo cp -r ./INSTALL/* /
sudo chmod a+x /usr/local/bin/kernelstub
sudo chmod a+x /etc/kernel/postinst.d/zz-kernelstub

echo "Installation complete! Don't forget to create a file in /etc/default/kernelstub"
echo "with your required kernel parameters/options. You likely need to use:"
echo ""
echo " quiet splash" 
echo ""
echo "for your parameters. You can get the full list from /proc/cmdline, but note "
echo "that you don't need the 'root=' or 'initrd=' options, if present."
