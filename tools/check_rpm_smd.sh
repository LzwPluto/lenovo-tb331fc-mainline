#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts

echo "=== OUR dts: rpm-smd provider? ==="
grep -n "rpm-smd\|rpm-requests\|qcom,rpmcc\|smd-edge" "$C" | head -8
echo "count rpm-smd: $(grep -c 'rpm-smd' "$C")"

echo
echo "=== VENDOR: rpm-smd provider ==="
grep -n "qcom,rpm-smd\b\|rpm-requests" "$V" | head -5

echo
echo "=== VENDOR: pm6125@0 regulators block (first 40 lines) ==="
awk 'NR>=5913 && NR<=5965' "$V"
