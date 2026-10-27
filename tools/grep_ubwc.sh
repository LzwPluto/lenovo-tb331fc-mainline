#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== where ubwc_*_version is set ==="
grep -rn "ubwc_enc_version\|ubwc_dec_version" drivers/gpu/drm/msm/ include/ 2>/dev/null | head -20

echo
echo "=== DT property names ==="
grep -rn "ubwc" drivers/gpu/drm/msm/disp/dpu1/dpu_kms.c drivers/gpu/drm/msm/disp/dpu1/dpu_hw_catalog.c 2>/dev/null | head -15

echo
echo "=== msm_mdss / catalog ubwc config on sm6225 ==="
grep -rn -B3 -A6 "ubwc" drivers/gpu/drm/msm/disp/dpu1/catalog/dpu_*.c 2>/dev/null | grep -iE "sm6225|sc7280|ubwc" | head -20
