#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
for o in USB_CONFIGFS_MASS_STORAGE USB_CONFIGFS_ACM USB_CONFIGFS_RNDIS \
         USB_F_MASS_STORAGE USB_CONFIGFS USB_GADGET BLK_DEV_LOOP; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    if [ -z "$v" ]; then
        printf "  %-30s NOT SET\n" "$o"
    else
        printf "  %-30s %s\n" "$o" "$v"
    fi
done
