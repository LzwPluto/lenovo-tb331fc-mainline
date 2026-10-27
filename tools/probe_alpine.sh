#!/bin/bash
# Probe Alpine availability for aarch64 + niri, and check our current initramfs
# busybox for the tools we will need at boot (losetup, mount, switch_root).
set -e
cd /mnt/d/TB331FCLinux
mkdir -p rootfs/alpine
cd rootfs/alpine

echo "=== network ==="
curl -sI https://dl-cdn.alpinelinux.org/alpine/ | head -2

echo
echo "=== latest alpine releases ==="
curl -s https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/aarch64/ \
    | grep -oE 'alpine-minirootfs-[0-9.]+-aarch64\.tar\.gz' | sort -u | tail -3

echo
echo "=== apk-tools-static (x86_64) ==="
curl -s https://dl-cdn.alpinelinux.org/alpine/latest-stable/main/x86_64/ \
    | grep -oE 'apk-tools-static-[0-9][^"]*x86_64\.apk' | sort -u | tail -2

echo
echo "=== does Alpine have niri for aarch64? (community) ==="
for repo in community main testing; do
    printf "  %-10s " "$repo"
    curl -s "https://dl-cdn.alpinelinux.org/alpine/edge/$repo/aarch64/" \
        | grep -oE 'niri-[0-9][^"]*\.apk' | sort -u | tail -2 | tr '\n' ' '
    echo
done

echo
echo "=== mesa / freedreno packages ==="
curl -s https://dl-cdn.alpinelinux.org/alpine/edge/main/aarch64/ \
    | grep -oE 'mesa-[a-z]*-[0-9][^"]*aarch64\.apk' | sort -u | head -8

echo
echo "=== busybox applets we depend on ==="
/mnt/d/TB331FCLinux/rootfs/busybox --list 2>/dev/null | grep -E '^(losetup|mount|switch_root|insmod|modprobe|chroot)$' | tr '\n' ' '
echo
