#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts

echo "=== OUR dts: rpm-smd-regulator / pm6125 / spmi ==="
grep -cE "rpm-smd-regulator" "$C"
grep -cE "pm6125" "$C"
grep -nE "pm6125@|spmi|regulators \{" "$C" | head -8

echo
echo "=== VENDOR dts: rpm-smd-regulator count ==="
grep -cE "rpm-smd-regulator" "$V"
grep -nE "regulators \{|pm6125_rpm|pm6125@0" "$V" | head -6

echo
echo "=== OUR dts: what our supplies (0x4c/0x59/0xa8/0xa9) point to ==="
for ph in 0x4c 0x59 0xa8 0xa9; do
    ln=$(grep -n "phandle = <$ph>" "$C" | head -1 | cut -d: -f1)
    echo "--- $ph (line ${ln:-none}) ---"
    [ -n "$ln" ] && sed -n "$((ln-14)),${ln}p" "$C" | grep -E "compatible|regulator-name|^\t+[a-z0-9_-]+ \{" | tail -3
done
