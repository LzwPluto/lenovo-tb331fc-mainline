#!/bin/bash
# Stage 1: extract the Alpine aarch64 minirootfs and cross-install packages.
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine

STAGE=stage
rm -rf "$STAGE"
mkdir -p "$STAGE"

echo "=== extract minirootfs ==="
tar -xzf alpine-minirootfs-3.24.3-aarch64.tar.gz -C "$STAGE" \
    --no-same-owner --no-same-permissions 2>&1 | head -5 || true
echo "  files: $(find "$STAGE" -type f | wc -l)"
ls "$STAGE"

echo
echo "=== apk version inside rootfs ==="
ls "$STAGE/sbin/apk" 2>/dev/null || echo "  (no apk)"

echo
echo "=== cross-install packages (aarch64) ==="
./apk.static --root "$STAGE" --arch aarch64 --initdb --no-progress \
    --keys-dir "$STAGE/etc/apk/keys" \
    --repository https://dl-cdn.alpinelinux.org/alpine/v3.24/main \
    --repository https://dl-cdn.alpinelinux.org/alpine/v3.24/community \
    --allow-untrusted \
    add alpine-base mesa mesa-dri-gallium mesa-egl mesa-gbm \
        libdrm eudev niri 2>&1 | tail -25

echo
echo "=== result ==="
echo "  files: $(find "$STAGE" -type f | wc -l)"
du -sh "$STAGE"
ls "$STAGE/usr/bin" 2>/dev/null | grep -iE 'niri|weston|modetest' | head
