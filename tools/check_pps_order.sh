#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c
echo "=== PPS / 0x11 相关函数 ==="
grep -n "p255_inx_replay_range\|p255_inx_init\|pps_payload_pack\|picture_parameter_set\|compression_mode_ext\|stop_before_0x11\|0x11" "$F" | head -25
echo
echo "=== lenovo_p255_inx_init 完整实现 ==="
LN=$(grep -n "static int lenovo_p255_inx_init\|p255_inx_init(struct" "$F" | head -1 | cut -d: -f1)
echo "at line $LN"
[ -n "$LN" ] && sed -n "$((LN-5)),$((LN+45))p" "$F"
