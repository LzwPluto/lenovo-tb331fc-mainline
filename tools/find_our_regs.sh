#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
for r in pm6125_l9 pm6125_l16 pm6125_l17 pm6125_l23; do
    echo "=== $r in OUR dts ==="
    ln=$(grep -n "$r" "$C" | head -1 | cut -d: -f1)
    if [ -n "$ln" ]; then
        end=$((ln+14))
        sed -n "${ln},${end}p" "$C" | grep -E "regulator-name|regulator-min|phandle" | head -2
    else
        echo "  not found by name"
    fi
done
echo
echo "=== 我们的 DTS 里 regulator 节点是如何命名的（前 12 个）==="
grep -nE "^\t+[a-z0-9_-]*(l[0-9]+|s[0-9]+|bob)[a-z0-9_-]* \{" "$C" | head -12
