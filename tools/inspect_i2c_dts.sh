#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1

echo "=== i2c@4a84000 node in our canonical DTS ==="
grep -n -A12 'i2c@4a84000' CANONICAL_383_dma.dts | head -20

echo
echo "=== how are GPIOs referenced (touch node example)? ==="
grep -n 'novatek,irq-gpio\|novatek,reset-gpio\|interrupts = ' CANONICAL_383_dma.dts | head -6

echo
echo "=== tlmm node phandle ==="
grep -n -B2 -A4 'pinctrl@4b00000\|tlmm' CANONICAL_383_dma.dts | head -20

echo
echo "=== existing regulator-fixed nodes (style reference) ==="
grep -n -A8 'regulator-fixed' CANONICAL_383_dma.dts | head -24

echo
echo "=== symbols? (dtc -@ output) ==="
grep -c '__symbols__' CANONICAL_383_dma.dts
