#!/bin/bash
set +e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== QRTR / QMI config ==="
for o in QRTR QRTR_SMD QRTR_MHI QRTR_TUN QCOM_QMI_HELPERS \
         QCOM_GLINK QCOM_SMEM QCOM_SMD_RPM QCOM_RPROC_COMMON \
         QCOM_PDR_HELPERS QCOM_PDR_MSG QCOM_SYSMON ATH10K_QMI; do
    v=$(grep -E "^CONFIG_${o}=" .config || true)
    v2=$(grep -E "^# CONFIG_${o} is not set" .config || true)
    if [ -n "$v" ]; then printf "  %-22s %s\n" "$o" "$v"
    elif [ -n "$v2" ]; then printf "  %-22s NOT SET\n" "$o"
    else printf "  %-22s (absent)\n" "$o"; fi
done
