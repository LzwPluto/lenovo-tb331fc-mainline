#!/bin/bash
# Download the Alpine aarch64 minirootfs and a host-side static apk so we can
# cross-install packages without qemu/chroot.
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine

MR=alpine-minirootfs-3.24.3-aarch64.tar.gz
if [ ! -f "$MR" ]; then
    echo "downloading $MR ..."
    curl -s -o "$MR" "https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/aarch64/$MR"
fi
ls -l "$MR"

echo
echo "=== find apk-tools-static ==="
curl -s https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/ > list.html
grep -o 'apk-tools-static-[0-9][^"<]*\.apk' list.html | sort -u | tail -3 > apklist.txt
cat apklist.txt
APK=$(tail -1 apklist.txt)
if [ -n "$APK" ]; then
    curl -s -o apk-tools-static.apk "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/$APK"
    ls -l apk-tools-static.apk
    rm -rf apkstatic && mkdir apkstatic
    tar -xzf apk-tools-static.apk -C apkstatic 2>/dev/null
    find apkstatic -name 'apk.static' -o -name 'apk' -type f | head -3
    cp "$(find apkstatic -name 'apk.static' | head -1)" ./apk.static
    chmod +x apk.static
    ./apk.static --version
fi

echo
echo "=== busybox applets (losetup/mount/switch_root) ==="
for a in losetup mount switch_root insmod modprobe; do
    if /mnt/d/TB331FCLinux/rootfs/busybox --list 2>/dev/null | grep -qx "$a"; then
        echo "  $a: yes"
    else
        echo "  $a: NO"
    fi
done
