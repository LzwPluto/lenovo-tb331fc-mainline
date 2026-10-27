#!/usr/bin/env python3
"""add_switchroot.py - make init hand over to the Alpine rootfs image on the SD card.

exec keeps PID 1, which busybox switch_root requires.
"""
import sys

import os
P = '/mnt/d/TB331FCLinux/initramfs/init_v5.c'
if not os.path.exists(P):
    P = r'D:\TB331FCLinux\initramfs\init_v5.c'
t = open(P, encoding='utf-8').read()

if 'alpine-rootfs.img' in t:
    print('already patched')
    sys.exit(0)

ANCHOR = "    /* If the kernel cannot mount the partition, pull the script out of the raw"

ADD = (
    "    /* If the SD card carries an ext4 rootfs image, hand over to it.  exec\n"
    "     * keeps us as PID 1, which busybox switch_root requires. */\n"
    "    if (card_mounted && access(\"/mnt/alpine-rootfs.img\", R_OK) == 0) {\n"
    "        printf(\"\\n[init] found /mnt/alpine-rootfs.img -> switching root\\n\");\n"
    "        fflush(stdout);\n"
    "        char *const sv[] = { \"/bin/busybox\", \"sh\", \"/switchroot.sh\", NULL };\n"
    "        execv(\"/bin/busybox\", sv);\n"
    "        printf(\"[init] exec switchroot.sh failed\\n\");\n"
    "    }\n"
    "\n"
)

if ANCHOR not in t:
    sys.exit('anchor not found')

t = t.replace(ANCHOR, ADD + ANCHOR, 1)
open(P, 'w', encoding='utf-8', newline='\n').write(t)
print('init: switchroot hook added')
