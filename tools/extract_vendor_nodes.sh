#!/bin/bash
set +e
D=/mnt/d/TB331FCLinux/ref/android/vendor.dts

echo "=== where is wcn3990-bt / wcn3990-wifi ==="
grep -n "wcn3990-bt\|wcn3990-wifi" "$D" | head -5

echo
echo "=== bluetooth node context ==="
grep -n -B30 "wcn3990-bt" "$D" | grep -E "serial@|bluetooth \{|compatible = \"qcom,wcn|pinctrl|interrupts|status" | head -12

echo
echo "=== wifi node context ==="
grep -n -A14 "wcn3990-wifi" "$D" | head -18

echo
echo "=== touch controllers in vendor DT ==="
grep -nE "novatek|nt36523|nt36|himax|hx83102|touchscreen@" "$D" | head -12
