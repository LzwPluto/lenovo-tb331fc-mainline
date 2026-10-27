#!/bin/bash
set +e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== regulator drivers in kernel config ==="
for o in REGULATOR REGULATOR_QCOM_RPM REGULATOR_QCOM_RPMH \
         REGULATOR_QCOM_SMD_RPM REGULATOR_QCOM_SPMI QCOM_SMD_RPM; do
    v=$(grep -E "^CONFIG_${o}=" .config || true)
    if [ -z "$v" ]; then printf "  %-26s NOT SET\n" "$o"; else printf "  %-26s %s\n" "$o" "$v"; fi
done

echo
echo "=== vendor: how many regulator blocks and under which PMICs ==="
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
grep -nE "regulators \{|qcom,pm[a-z0-9]+@" "$V" | head -20
