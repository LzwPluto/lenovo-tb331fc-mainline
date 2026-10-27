#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== ath10k 里固件名的定义 ==="
grep -rn "wlanmdsp\|bdwlan\|fw_name\|board.*\.bin" drivers/net/wireless/ath/ath10k/*.c drivers/net/wireless/ath/ath10k/*.h 2>/dev/null | grep -iE "wlanmdsp|bdwlan|fw_name" | head -15
echo
echo "=== qmi.c 里请求的固件 ==="
grep -rn -B2 -A4 "request_firmware\|ath10k_qmi_load_bdf\|fw_name" drivers/net/wireless/ath/ath10k/qmi.c 2>/dev/null | head -30
