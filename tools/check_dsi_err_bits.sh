#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
F=$K/drivers/gpu/drm/msm/dsi/dsi_display.c
echo "=== dsi_err_worker 打印 status 的地方 ==="
grep -n -B8 "dsi_err_worker" "$F" | head -20
echo
echo "=== 错误位定义 ==="
grep -rnE "DSI_ERROR_(ACK|TIMEOUT|FIFO|LP_RX|ECC|CRC|UNDER|OVER)[A-Z_]*\s*=" "$K/drivers/gpu/drm/msm/dsi/"*.h "$K/drivers/gpu/drm/msm/dsi/"*.c 2>/dev/null | head -20
echo
echo "=== dsi_error 结构/掩码 ==="
grep -rn "DSI_ERROR_" "$K/drivers/gpu/drm/msm/dsi/dsi_host.c" | head -20
