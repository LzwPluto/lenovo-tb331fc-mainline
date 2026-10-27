#!/bin/bash
set +e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== debug-related config ==="
for o in ATH10K_DEBUG ATH10K_DEBUGFS ATH10K_TRACING DYNAMIC_DEBUG \
         DEBUG_FS ATH10K_QMI QCOM_QMI_HELPERS QRTR; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    if [ -n "$v" ]; then printf "  %-20s %s\n" "$o" "$v"
    else printf "  %-20s NOT SET\n" "$o"; fi
done
echo
echo "=== ath10k debug_mask parameter exists? ==="
grep -rn "debug_mask" drivers/net/wireless/ath/ath10k/core.c | head -5
echo
echo "=== does ath10k_qmi log service wait failures at debug level? ==="
grep -n "ath10k_dbg\|ath10k_err\|ath10k_warn" drivers/net/wireless/ath/ath10k/qmi.c | head -20
