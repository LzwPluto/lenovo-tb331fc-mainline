#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== Kconfig entry ==="
grep -rn -A12 "config QCOM_ZAP_SHADER" --include=Kconfig . | head -20
echo
echo "=== source file ==="
find . -name "*zap*" -path "*firmware*" | head -10
echo
echo "=== QCOM_SCM / QCOM_MDT_LOADER / QCOM_SMEM state ==="
for o in QCOM_SCM QCOM_MDT_LOADER QCOM_SMEM QCOM_RPROC_COMMON; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    [ -z "$v" ] && printf "  %-24s NOT SET\n" "$o" || printf "  %-24s %s\n" "$o" "$v"
done
