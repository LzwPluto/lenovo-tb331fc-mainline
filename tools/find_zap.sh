#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== files mentioning zap ==="
grep -rln "zap.shader\|zap_shader" --include=*.c --include=*.h --include=Kconfig . | head -10
echo
echo "=== how adreno loads it ==="
grep -rn -B4 -A18 "zap_shader\|zap-shader" drivers/gpu/drm/msm/adreno/adreno_gpu.c | head -60
