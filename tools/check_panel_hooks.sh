#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c
echo "=== 面板驱动的 prepare/enable/disable/unprepare 钩子 ==="
grep -nE "static int hx83102_(prepare|enable|disable|unprepare)|\.prepare|\.enable|\.disable|\.unprepare|struct drm_panel_funcs" "$F" | head -20
echo
echo "=== 钩子函数本体（enable/disable）==="
for fn in enable disable; do
  LN=$(grep -n "static int hx83102_${fn}(" "$F" | head -1 | cut -d: -f1)
  if [ -n "$LN" ]; then
    echo "--- hx83102_${fn} at $LN ---"
    sed -n "${LN},$((LN+22))p" "$F"
    echo
  fi
done
echo "=== 这个面板驱动是否只服务 p255 一台设备 ==="
grep -n "of_device_id\|compatible =" "$F" | head -8
