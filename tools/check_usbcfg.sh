#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
for o in USB_CONFIGFS USB_CONFIGFS_ACM USB_GADGET USB_DWC3 USB_DWC3_QCOM \
         USB_GADGET_SERIAL USB_LIBCOMPOSITE USB_CONFIGFS_ECM USB_F_ACM; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    if [ -z "$v" ]; then
        printf "  %-22s NOT SET\n" "$o"
    else
        printf "  %-22s %s\n" "$o" "$v"
    fi
done
echo
echo "=== related USB lines in .config ==="
grep -E "CONFIG_USB_(GADGET|DWC3|CONFIGFS|LIBCOMPOSITE)" .config | head -20
