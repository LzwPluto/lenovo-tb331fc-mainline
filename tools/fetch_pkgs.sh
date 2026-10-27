#!/bin/bash
# Download the packages niri needs (and a few debug tools) into a folder we can
# copy to the SD card, then install them inside Alpine with `apk add <file>`.
# No network needed on the device, and no image rebuild.
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine

MIRROR=https://mirrors.tuna.tsinghua.edu.cn/alpine
VER=v3.24
OUT=/mnt/d/TB331FCLinux/rootfs/alpine/apks

rm -rf "$OUT"; mkdir -p "$OUT"

PKGS="wayland-libs-server seatd mesa-utils evtest"

echo "=== installing into stage (fills /var/cache/apk) ==="
./apk.static --root stage --arch aarch64 --usermode --no-progress \
    --keys-dir stage/etc/apk/keys \
    --repository "$MIRROR/$VER/main" \
    --repository "$MIRROR/$VER/community" \
    --allow-untrusted \
    add $PKGS 2>&1 | tail -20

echo
echo "=== collecting .apk files ==="
cp stage/var/cache/apk/*.apk "$OUT"/ 2>/dev/null || true
ls -1 "$OUT" | head -40
echo "  total: $(ls -1 "$OUT" | wc -l) files, $(du -sh "$OUT" | cut -f1)"
