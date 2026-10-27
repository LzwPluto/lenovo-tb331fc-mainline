#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1

echo "=== does the flashed DTB carry __symbols__? ==="
dtc -I dtb -O dts CANONICAL_oppfix.dtb 2>/dev/null | grep -c '__symbols__'
echo "symbols:"
dtc -I dtb -O dts CANONICAL_oppfix.dtb 2>/dev/null | sed -n '/__symbols__ {/,/};/p' | grep -c '= "'

echo
echo "=== reproduce the build: plain dtc vs -@ ==="
dtc -I dts -O dtb -o /tmp/plain.dtb CANONICAL_oppfix.dts 2>/dev/null
dtc -@ -I dts -O dtb -o /tmp/atsym.dtb CANONICAL_oppfix.dts 2>/dev/null
ls -l CANONICAL_oppfix.dtb /tmp/plain.dtb /tmp/atsym.dtb 2>/dev/null
for f in /tmp/plain.dtb /tmp/atsym.dtb; do
    if cmp -s "$f" CANONICAL_oppfix.dtb; then echo "IDENTICAL: $f"; else echo "differs:   $f"; fi
done
