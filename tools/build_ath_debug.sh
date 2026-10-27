#!/bin/bash
# Rebuild the kernel Image with ath10k debug support so that
#   echo 0xffffffff > /sys/module/ath10k_core/parameters/debug_mask
# makes the driver print where it blocks (QMI service wait, firmware path, ...).
set +e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== enable debug options (built-in ath10k -> only Image changes) ==="
./scripts/config --enable ATH10K_DEBUG
./scripts/config --enable ATH10K_DEBUGFS
./scripts/config --enable DEBUG_FS
./scripts/config --disable DYNAMIC_DEBUG
make ARCH=arm64 olddefconfig 2>&1 | tail -3

echo "=== verify ==="
for o in ATH10K_DEBUG ATH10K_DEBUGFS ATH10K ATH10K_SNOC; do
    grep -E "^CONFIG_${o}=" .config || echo "  CONFIG_${o} not set"
done

echo "=== build Image ==="
time make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 | tail -12
ls -l arch/arm64/boot/Image
