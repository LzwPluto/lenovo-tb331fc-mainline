#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c
echo "=== 我们的 p255_inx 初始化序列 ==="
grep -c "0x" "$F"
echo
echo "=== 关键标记检查 ==="
for pat in "0xFF, 0x10" "0xFB, 0x01" "0x91" "0x92" "0x93" "0x94" "0x95" "0x96" "0x25" "0x30" "0x39" "0x84" "0x85"; do
    n=$(grep -c "0x${pat#0x}, " "$F" 2>/dev/null)
    n2=$(grep -c "${pat}" "$F" 2>/dev/null)
    printf "  %-12s 出现 %s 次\n" "$pat" "$n2"
done
echo
echo "=== ESD 段（0xFF,0x25 之后的 0x91..0x96）==="
grep -n -A10 "0x91" "$F" | head -20
echo
echo "=== pen 段（0x25/0x30/0x39）==="
grep -n "0x25, \|0x30, \|0x39, " "$F" | head -10
