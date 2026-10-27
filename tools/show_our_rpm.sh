#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== our DTS around line 400-450 ==="
sed -n '400,450p' "$C"
echo
echo "=== does our DTS have 'rpm-requests' and under what parent? ==="
grep -n "rpm-requests\|compatible = \"qcom,rpm" "$C" | head -8
