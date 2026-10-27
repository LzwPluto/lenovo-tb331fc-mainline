#!/bin/bash
# Fetch a truly static aarch64 busybox from Ubuntu ports and verify it.
set -e
cd /mnt/d/TB331FCLinux
mkdir -p rootfs
rm -rf rootfs/bb.deb rootfs/ex

echo "=== query ports.ubuntu.com for busybox-static arm64 ==="
INDEX=$(curl -s http://ports.ubuntu.com/ubuntu-ports/pool/main/b/busybox/)
PKG=$(printf '%s' "$INDEX" | tr '"' '\n' | grep -E '^busybox-static_.*arm64\.deb$' | sort -u | tail -1)
if [ -z "$PKG" ]; then
  echo "!! package not found in index"
  printf '%s' "$INDEX" | head -c 400
  exit 1
fi
echo "package: $PKG"

URL="http://ports.ubuntu.com/ubuntu-ports/pool/main/b/busybox/$PKG"
curl -s -o rootfs/bb.deb "$URL"
ls -l rootfs/bb.deb

mkdir -p rootfs/ex
dpkg-deb -x rootfs/bb.deb rootfs/ex
BB=$(find rootfs/ex -name busybox -type f | head -1)
echo "extracted: $BB"
ls -l "$BB"
file "$BB"
cp "$BB" rootfs/busybox
chmod +x rootfs/busybox
echo "=== ready: rootfs/busybox ==="
