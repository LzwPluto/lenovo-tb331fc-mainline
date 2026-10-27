#!/bin/bash
cd /mnt/d/TB331FCLinux || exit 1

echo "=== vendor bkl-bl@11 node with context (ov2.dts) ==="
sed -n '3020,3060p' build/ov2.dts

echo
echo "=== which i2c controller is its parent? search upwards for i2c@ ==="
awk 'NR<=3040 && /i2c@[0-9a-f]+/ {line=NR": "$0} END{}  {if(NR==3040) print "last i2c seen -> " line}' build/ov2.dts

echo
echo "=== all i2c controllers in ov2.dts ==="
grep -nE 'i2c@[0-9a-f]+|^\t+[a-z0-9_]+: i2c' build/ov2.dts | head -20

echo
echo "=== mainline ktz8866 binding ==="
cat ~/kbuild/linux-next-tb128fu-hx83102-panel-port/Documentation/devicetree/bindings/leds/backlight/kinetic,ktz8866.yaml 2>/dev/null | head -70
