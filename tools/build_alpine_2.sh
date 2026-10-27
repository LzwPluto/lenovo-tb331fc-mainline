#!/bin/bash
# Cross-install Alpine aarch64 packages into the staged rootfs using a Chinese
# mirror. apk.static is x86_64 so no qemu/chroot is needed; --usermode is
# required because we are not root.
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine

MIRROR=${MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/alpine}
VER=v3.24

echo "=== mirror: $MIRROR ==="
curl -sI "$MIRROR/$VER/main/aarch64/APKINDEX.tar.gz" | head -2

echo
echo "=== installing packages ==="
./apk.static --root stage --arch aarch64 --usermode --no-progress \
    --keys-dir stage/etc/apk/keys \
    --repository "$MIRROR/$VER/main" \
    --repository "$MIRROR/$VER/community" \
    --allow-untrusted \
    add alpine-base mesa mesa-dri-gallium mesa-egl mesa-gbm \
        libdrm eudev niri

echo
echo "=== result ==="
echo "  files: $(find stage -type f | wc -l)"
du -sh stage
echo "  niri: $(ls stage/usr/bin/niri 2>/dev/null || echo MISSING)"
echo "  mesa: $(find stage -name 'msm_dri.so' -o -name '*freedreno*' 2>/dev/null | head -3)"
