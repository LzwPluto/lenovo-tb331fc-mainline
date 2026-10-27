#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
for o in BLK_DEV_LOOP EXT4_FS VFAT_FS MSDOS_FS OVERLAY_FS SQUASHFS DEVTMPFS TMPFS; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    [ -z "$v" ] && printf "  %-18s NOT SET\n" "$o" || printf "  %-18s %s\n" "$o" "$v"
done
