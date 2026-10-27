#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== QCOM_RPROC_COMMON Kconfig ==="
grep -A6 "^config QCOM_RPROC_COMMON" drivers/remoteproc/Kconfig
echo
echo "=== current values ==="
for o in REMOTEPROC QCOM_RPROC_COMMON QCOM_SCM QCOM_SMEM QCOM_QMI_HELPERS; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    if [ -z "$v" ]; then printf "  %-22s NOT SET\n" "$o"; else printf "  %-22s %s\n" "$o" "$v"; fi
done
