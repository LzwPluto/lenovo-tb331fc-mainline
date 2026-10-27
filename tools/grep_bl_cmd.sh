#!/bin/bash
cd /mnt/d/TB331FCLinux || exit 1

F=$(find . -name 'p255_inx_init.h' 2>/dev/null | head -1)
echo "file = $F"
[ -z "$F" ] && exit 0

echo
echo "=== entries containing 0x51 (DCS write display brightness) ==="
grep -n '0x51' "$F" | head -20

echo
echo "=== entries containing 0x53 (write control display) ==="
grep -n '0x53' "$F" | head -10

echo
echo "=== page-select (0xFF) entries, to know which bank 0x51 lives in ==="
grep -n '0xff' "$F" | head -20

echo
echo "=== total command count and first/last few lines ==="
head -12 "$F"
echo "..."
tail -12 "$F"
