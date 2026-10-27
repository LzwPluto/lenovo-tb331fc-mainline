#!/bin/bash
# Build an initramfs that carries both the touch and the GPU firmware.
set -e
IR=/mnt/d/TB331FCLinux/initramfs
FW=/mnt/d/TB331FCLinux/firmware/vendor-firmware
STAGE=$IR/r15

rm -rf "$STAGE"
mkdir -p "$STAGE/lib/firmware/qcom/sm6225/LENOVO/TB128FU"

cp "$IR/init_v12"        "$STAGE/init"
cp /mnt/d/TB331FCLinux/rootfs/busybox "$STAGE/busybox"
cp "$IR/diag.sh"         "$STAGE/diag.sh"
cp "$IR/gadget.sh"       "$STAGE/gadget.sh"
chmod +x "$STAGE/busybox" "$STAGE/diag.sh" "$STAGE/gadget.sh"

# touch firmware
cp "$FW/novatek_ts_fw.bin"  "$STAGE/lib/firmware/"
cp "$FW/Himax_firmware.bin" "$STAGE/lib/firmware/"

# GPU firmware
cp "$FW/a630_sqe.fw" "$STAGE/lib/firmware/qcom/"
cp "$FW/a610_zap.mdt" "$FW/a610_zap.b00" "$FW/a610_zap.b01" "$FW/a610_zap.b02" \
   "$STAGE/lib/firmware/qcom/sm6225/LENOVO/TB128FU/"

echo "--- staged firmware ---"
find "$STAGE/lib" -type f -printf '%10s  %p\n' | sed "s#$STAGE/##"

cd "$STAGE"
find . | cpio -o -H newc 2>/dev/null > "$IR/initramfs_v15.cpio"
echo "--- cpio ---"
ls -l "$IR/initramfs_v15.cpio"
