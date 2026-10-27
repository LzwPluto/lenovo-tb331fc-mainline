#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== hx83102 panel driver 里有 DSC 吗 ==="
grep -in "dsc\|compression" drivers/gpu/drm/panel/panel-himax-hx83102.c | head -10
echo
echo "=== 其他 DSC 面板驱动示例 ==="
grep -rln "drm_dsc_config" drivers/gpu/drm/panel/ | head -8
echo
echo "=== msm dsi 的 DSC 支持 ==="
grep -rn "dsc" drivers/gpu/drm/msm/dsi/dsi_host.c | head -12
echo
echo "=== sm6225 dsi 支持 dsc? ==="
grep -rn "dsc" drivers/gpu/drm/msm/dsi/phy/dsi_phy_14nm.c 2>/dev/null | head -5
echo
echo "=== vendor p255_inx 的 dsc 参数 ==="
python3 - <<'PY'
import re
t=open(r'/mnt/d/TB331FC_GSI_Kit/device_specific_backup/tb331fc_stock.dts',encoding='utf-8',errors='replace').read()
m=re.search(r'^[ \t]*(qcom,mdss_dsi_panel_p255_inx_fhd_video)[ \t]*\{', t, re.M)
j=t.index('{',m.start()); depth=0; k=j
while k<len(t):
    if t[k]=='{': depth+=1
    elif t[k]=='}':
        depth-=1
        if depth==0: break
    k+=1
body=t[j+1:k]
for p in ('qcom,compression-mode','qcom,mdss-dsc-version','qcom,mdss-dsc-scr-version',
          'qcom,mdss-dsc-bit-per-pixel','qcom,mdss-dsc-bit-per-component',
          'qcom,mdss-dsc-slice-width','qcom,mdss-dsc-slice-height',
          'qcom,mdss-dsc-slice-per-pkt','qcom,mdss-dsi-lane-map',
          'qcom,mdss-dsi-h-sync-pulse','qcom,mdss-dsi-color-order',
          'qcom,mdss-pan-physical-width-dimension','qcom,mdss-pan-physical-height-dimension'):
    mm=re.search(r'^[ \t]*'+re.escape(p)+r'\s*=\s*([^;]+);', body, re.M)
    if mm:
        print(f'  {p:<40} {mm.group(1).strip()}')
PY
