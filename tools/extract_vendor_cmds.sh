#!/bin/bash
# 提取厂商 4 个初始化命令函数的实际命令字节/参数
set +e
D=/mnt/d/TB331FCLinux/ref/nvt36523_spi.dis
A=/mnt/d/TB331FCLinux/tools/analyze_nvt_workfunc.py

for f in nvt_edge_reject_set nvt_edge_grid_zone_set nvt_game_mode_set nvt_support_pen_set; do
    echo "===== $f ====="
    python3 "$A" "$D" "$f" 2>/dev/null \
        | grep -E 'mov +w[0-9]+, #0x|bl .*<(nvt_cmd_store|nvt_ext_cmd_store|nvt_write_addr|msleep)' \
        | head -14
    echo
done
