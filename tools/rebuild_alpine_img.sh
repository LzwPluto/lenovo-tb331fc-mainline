#!/bin/bash
# Put the firmware into the Alpine rootfs and rebuild the ext4 image.
# (After switch_root the initramfs /lib/firmware is no longer visible, so the
# touch and GPU firmware must live inside the Alpine image itself.)
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine
STAGE=stage
FW=/mnt/d/TB331FCLinux/firmware/vendor-firmware

echo "=== firmware into rootfs ==="
mkdir -p "$STAGE/lib/firmware/qcom/sm6225/LENOVO/TB128FU"
cp "$FW/novatek_ts_fw.bin"  "$STAGE/lib/firmware/" 2>/dev/null || true
cp "$FW/Himax_firmware.bin" "$STAGE/lib/firmware/" 2>/dev/null || true
cp "$FW/a630_sqe.fw"        "$STAGE/lib/firmware/qcom/" 2>/dev/null || true
for f in a610_zap.mdt a610_zap.b00 a610_zap.b01 a610_zap.b02; do
    cp "$FW/$f" "$STAGE/lib/firmware/qcom/sm6225/LENOVO/TB128FU/" 2>/dev/null || true
done
find "$STAGE/lib/firmware" -type f -printf '%10s  %p\n' | sed "s#$STAGE/##"

echo
echo "=== root password (empty) so serial login works ==="
sed -i 's/^root:[^:]*:/root::/' "$STAGE/etc/shadow" 2>/dev/null || true
grep '^root:' "$STAGE/etc/shadow" | cut -d: -f1-3

echo
echo "=== rebuild image ==="
IMG=alpine-rootfs.img
rm -f "$IMG"
SIZE_MB=${SIZE_MB:-2560}
mke2fs -q -t ext4 -b 4096 -L alpine -d "$STAGE" -F "$IMG" "${SIZE_MB}M" 2>&1 | tail -3
ls -lh "$IMG"
