#!/bin/bash
set +u
SRC="/mnt/d/TB331FC_GSI_Kit/08_一键刷机/fw/NON-HLOS.bin"
OUT=/mnt/d/TB331FCLinux/firmware/nonhlos
MNT=/tmp/nh

echo "=== files in NON-HLOS image matching adsp/cdsp/modem/wlan ==="
if ! mountpoint -q "$MNT" 2>/dev/null; then
    mkdir -p "$MNT"
    sudo mount -o loop,ro "$SRC" "$MNT" || { echo "mount failed"; exit 1; }
fi
ls -l "$MNT/image" | grep -iE "adsp|cdsp|modem|wlan|slpi|wpss" | head -20

echo
echo "=== copying them ==="
mkdir -p "$OUT"
sudo cp "$MNT"/image/adsp*  "$OUT"/ 2>/dev/null
sudo cp "$MNT"/image/cdsp*  "$OUT"/ 2>/dev/null
sudo cp "$MNT"/image/modem* "$OUT"/ 2>/dev/null
sudo cp "$MNT"/image/slpi*  "$OUT"/ 2>/dev/null
sudo cp "$MNT"/image/wpss*  "$OUT"/ 2>/dev/null
sudo chown -R "$(id -u):$(id -g)" "$OUT" 2>/dev/null
sudo umount "$MNT" 2>/dev/null

echo "=== extracted to $OUT ==="
ls -l "$OUT" | grep -iE "adsp|cdsp|modem|slpi|wpss" | head -20
