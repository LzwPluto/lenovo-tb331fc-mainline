#!/bin/bash
# Make QCOM_RPROC_COMMON =y so ATH10K_SNOC can be =y.  It is a hidden tristate
# selected by the Q6V5 remoteproc drivers, so those have to be =y as well.
set -e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port

./scripts/config --file .config \
    --enable QCOM_Q6V5_COMMON \
    --enable QCOM_Q6V5_PAS \
    --enable QCOM_Q6V5_MSS \
    --enable QCOM_Q6V5_WCSS \
    --enable QCOM_RPROC_COMMON \
    --enable QCOM_QMI_HELPERS \
    --enable ATH10K_SNOC \
    --enable ATH10K \
    --enable QCOM_WCNSS 2>/dev/null || true

make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j10 olddefconfig >/dev/null 2>&1

echo "=== after olddefconfig ==="
for o in QCOM_Q6V5_PAS QCOM_Q6V5_COMMON QCOM_RPROC_COMMON QCOM_QMI_HELPERS \
         ATH10K ATH10K_SNOC QCOM_WCNSS; do
    v=$(grep -E "^CONFIG_${o}=" .config)
    if [ -z "$v" ]; then printf "  %-22s NOT SET\n" "$o"; else printf "  %-22s %s\n" "$o" "$v"; fi
done
