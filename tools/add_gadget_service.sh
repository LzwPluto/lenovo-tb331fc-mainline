#!/bin/bash
# Add the USB gadget service to the Alpine rootfs and rebuild the ext4 image.
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine
STAGE=stage

echo "=== install usbgadget service ==="
cp usbgadget.initd "$STAGE/etc/init.d/usbgadget"
chmod +x "$STAGE/etc/init.d/usbgadget"
mkdir -p "$STAGE/etc/runlevels/default"
ln -sf /etc/init.d/usbgadget "$STAGE/etc/runlevels/default/usbgadget"
ls -l "$STAGE/etc/init.d/usbgadget"
ls "$STAGE/etc/runlevels/default/"

echo
echo "=== also start it as early as possible (boot runlevel) ==="
mkdir -p "$STAGE/etc/runlevels/boot"
ln -sf /etc/init.d/usbgadget "$STAGE/etc/runlevels/boot/usbgadget" 2>/dev/null || true

echo
echo "=== keep the initramfs gadget as a fallback too ==="
echo "   (initramfs already creates one; Alpine's service recreates it after switch_root)"

echo
echo "=== rebuild image (2GiB) ==="
IMG=alpine-rootfs.img
rm -f "$IMG"
SIZE_MB=2048
mke2fs -q -t ext4 -b 4096 -L alpine -d "$STAGE" -F "$IMG" "${SIZE_MB}M" 2>&1 | tail -2
ls -lh "$IMG"
