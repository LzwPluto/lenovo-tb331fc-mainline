#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
echo "=== FB notifier / panel notifier ==="
grep -nE "fb_notif|fb_notifier|register_framebuffer|drm_panel|panel_notifier|notifier_block|FB_EVENT" "$F" | head -15
echo
echo "=== suspend/resume 注册 ==="
grep -nE "nvt_ts_suspend|nvt_ts_resume|dev_pm_ops|SIMPLE_DEV_PM_OPS" "$F" | head -10
echo
echo "=== CONFIG_FB 是否启用 ==="
grep -E "^CONFIG_FB=|^CONFIG_DRM_FBDEV" ~/kbuild/linux-next-tb128fu-hx83102-panel-port/.config
echo
echo "=== bTouchIsAwake 的使用 ==="
grep -n "bTouchIsAwake" "$F"
