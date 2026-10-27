#!/bin/bash
# Turn the WCN3990 WiFi/BT stack into built-ins.  ATH10K_SNOC and BT_HCIUART stay
# =m unless their tristate dependencies are also =y, so chase them down.
set -e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port

echo "=== Kconfig dependencies ==="
grep -rn -A6 "^config ATH10K_SNOC" drivers/net/wireless/ath/ath10k/Kconfig | head -10
grep -rn -A8 "^config BT_HCIUART$" drivers/bluetooth/Kconfig | head -12
echo

./scripts/config --file .config \
    --enable QCOM_QMI_HELPERS \
    --enable QCOM_SMEM \
    --enable QCOM_SMD_RPM \
    --enable QCOM_RPROC_COMMON \
    --enable SERIAL_DEV_BUS \
    --enable SERIAL_DEV_CTRL_TTYPORT \
    --enable NVMEM \
    --enable POWER_SEQUENCING \
    --enable TTY \
    --enable ATH10K \
    --enable ATH10K_SNOC \
    --enable BT \
    --enable BT_HCIUART \
    --enable BT_HCIUART_QCA \
    --enable BT_QCA \
    --enable QCOM_WCNSS 2>/dev/null || true

make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j10 olddefconfig >/dev/null 2>&1

echo "=== after olddefconfig ==="
for o in QCOM_QMI_HELPERS QCOM_RPROC_COMMON SERIAL_DEV_BUS NVMEM POWER_SEQUENCING \
         ATH10K ATH10K_SNOC BT BT_HCIUART BT_HCIUART_QCA BT_QCA; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    if [ -z "$v" ]; then printf "  %-22s NOT SET\n" "$o"; else printf "  %-22s %s\n" "$o" "$v"; fi
done
