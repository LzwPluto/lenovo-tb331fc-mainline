#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
for ph in 0x107 0x108 0x109 0x10a 0x10b 0x10c 0x10d 0x10e; do
    ln=$(grep -n "phandle = <$ph>" "$V" | head -1 | cut -d: -f1)
    if [ -z "$ln" ]; then
        echo "$ph : not found"
        continue
    fi
    # walk upwards to the node header and collect pins/function
    start=$((ln-10)); [ $start -lt 1 ] && start=1
    echo "=== $ph (line $ln) ==="
    sed -n "${start},$((ln))p" "$V" | grep -E "^\t+[a-z0-9_-]+ \{|pins =|function =|bias-|drive-strength" | tail -5
done
