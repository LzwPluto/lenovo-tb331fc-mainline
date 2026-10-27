#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
echo "=== msm_mdss.c 里 sm6225 的 UBWC 配置 ==="
grep -n -B4 -A18 "sm6225" "$K/drivers/gpu/drm/msm/msm_mdss.c" | head -40
echo
echo "=== 当前的 UBWC 相关补丁是否还在 ==="
grep -n "UBWC intentionally disabled\|ubwc" "$K/drivers/gpu/drm/msm/msm_mdss.c" | head -10
