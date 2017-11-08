#!/bin/bash

# Copyright 2017 Ian Santopietro <isantop@gmail.com>

#Permission to use, copy, modify, and/or distribute this software for any purpose
#with or without fee is hereby granted, provided that the above copyright notice
#and this permission notice appear in all copies.

#THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
#REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
#FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
#INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
#OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
#TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
#THIS SOFTWARE.



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
