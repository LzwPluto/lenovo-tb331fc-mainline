#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts

for ph in 0x83 0x84 0x85 0x86 0x4c 0x59 0xa8 0xa9; do
    echo "=== phandle $ph in VENDOR ==="
    ln=$(grep -n "phandle = <$ph>" "$V" | head -1 | cut -d: -f1)
    if [ -n "$ln" ]; then
        start=$((ln-12)); [ $start -lt 1 ] && start=1
        sed -n "${start},${ln}p" "$V" | grep -E "^\t+[a-z0-9_,@-]+ \{|regulator-name|regulator-min-microvolt|compatible" | tail -4
    else
        echo "  (not found)"
    fi
done

echo
echo "=== OUR DTS: regulator nodes and their names ==="
grep -nE "regulator-name = " "$C" | head -20
