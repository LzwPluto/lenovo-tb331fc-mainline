#!/bin/bash
# Stage 2: configure the Alpine rootfs for this tablet and pack it into an ext4
# image. Runs as non-root: mke2fs -d populates the image from a directory.
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine
STAGE=stage

echo "=== hostname / fstab / inittab ==="
echo "tb331fc" > "$STAGE/etc/hostname"
cat > "$STAGE/etc/hosts" <<'EOF'
127.0.0.1	localhost localhost.localdomain
::1		localhost localhost.localdomain
127.0.1.1	tb331fc
EOF

cat > "$STAGE/etc/fstab" <<'EOF'
# <fs>          <mountpoint> <type>  <options>            <dump> <pass>
/dev/root       /            ext4    rw,noatime           0 1
proc            /proc        proc    defaults             0 0
sysfs           /sys         sysfs   defaults             0 0
devtmpfs        /dev         devtmpfs mode=0755,nosuid    0 0
tmpfs           /dev/shm     tmpfs   nosuid,nodev         0 0
tmpfs           /run         tmpfs   mode=0755,nosuid     0 0
tmpfs           /tmp         tmpfs   nosuid,nodev         0 0
EOF

# getty on the USB serial gadget (ttyGS0) so the USB cable is a real console,
# plus an autologin root console on the DRM framebuffer.
cat > "$STAGE/etc/inittab" <<'EOF'
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::wait:/sbin/openrc default

# USB serial gadget console (so we can log in over USB-C)
ttyGS0::respawn:/sbin/getty -L ttyGS0 115200 vt100

# framebuffer consoles with root autologin for bring-up
tty1::respawn:/sbin/getty -n -l /bin/sh -L tty1 38400 linux
tty2::respawn:/sbin/getty -L tty2 38400 linux

::ctrlaltdel:/sbin/reboot
::shutdown:/sbin/openrc shutdown
EOF

echo "  /etc/inittab: $(grep -c getty "$STAGE/etc/inittab") getty entries"

echo
echo "=== enable a few services ==="
for s in devfs dmesg hwdrivers mdev; do
    [ -e "$STAGE/etc/init.d/$s" ] && ln -sf "/etc/init.d/$s" "$STAGE/etc/runlevels/sysinit/$s" 2>/dev/null && echo "  sysinit/$s"
done
for s in bootmisc hostname hwclock modules networking sysctl syslog urandom; do
    [ -e "$STAGE/etc/init.d/$s" ] && ln -sf "/etc/init.d/$s" "$STAGE/etc/runlevels/boot/$s" 2>/dev/null && echo "  boot/$s"
done
for s in udev udev-trigger udev-settle; do
    [ -e "$STAGE/etc/init.d/$s" ] && ln -sf "/etc/init.d/$s" "$STAGE/etc/runlevels/sysinit/$s" 2>/dev/null && echo "  sysinit/$s"
done

echo
echo "=== make /etc/apk usable on the device ==="
cat > "$STAGE/etc/apk/repositories" <<'EOF'
https://mirrors.tuna.tsinghua.edu.cn/alpine/v3.24/main
https://mirrors.tuna.tsinghua.edu.cn/alpine/v3.24/community
EOF

echo
echo "=== size before packing ==="
du -sh "$STAGE"

echo
echo "=== mke2fs support check ==="
mke2fs -V 2>&1 | head -1

IMG=alpine-rootfs.img
rm -f "$IMG"
SIZE_MB=${SIZE_MB:-2048}
echo "creating ${SIZE_MB}MB ext4 image populated from $STAGE ..."
mke2fs -q -t ext4 -b 4096 -L alpine -d "$STAGE" -F "$IMG" "${SIZE_MB}M" 2>&1 | tail -5
echo
ls -lh "$IMG"
echo "=== image contents (first 20) ==="
debugfs -R "ls -l /" "$IMG" 2>/dev/null | head -20
