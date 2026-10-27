#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== our regulators node content ==="
sed -n '486,520p' "$C"

echo
echo "=== upstream pm6125 rpm regulator definitions in the kernel tree ==="
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
ls arch/arm64/boot/dts/qcom/ | grep -i "pm6125" | head
echo "---"
grep -n "pm6125_l9\|pm6125_l23\|pm6125_l16\|pm6125_l17" arch/arm64/boot/dts/qcom/pm6125-rpm-regulator.dtsi 2>/dev/null | head -10
echo "--- file listing ---"
ls -l arch/arm64/boot/dts/qcom/pm6125*.dtsi 2>/dev/null
