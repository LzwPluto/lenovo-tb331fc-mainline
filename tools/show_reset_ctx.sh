#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
TS=drivers/input/touchscreen/nt36523_ts.c

echo "=== context around line 1069 ==="
sed -n '1050,1080p' "$TS"

echo
echo "=== context around line 1500 (two consecutive sw_reset_idle) ==="
sed -n '1488,1520p' "$TS"

echo
echo "=== the other reset helpers (365-400) ==="
sed -n '360,400p' "$TS"

echo
echo "=== does mainline 6.14 have drm_panel_follower? ==="
ls -l include/drm/drm_panel.h
grep -n "drm_panel_follower\|panel_prepared" include/drm/drm_panel.h | head -10
