#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts

echo "=== vendor: what is phandle 0x1b0 (vdd-cx-mx)? ==="
ln=$(grep -n "phandle = <0x1b0>" "$V" | head -1 | cut -d: -f1)
echo "  defined at line $ln"
start=$((ln-20)); [ $start -lt 1 ] && start=1
sed -n "${start},${ln}p" "$V" | grep -E "^\t+[a-z0-9_,@-]+ \{|regulator-name|regulator-min-microvolt|regulator-max-microvolt|compatible" | tail -6

echo
echo "=== vendor icnss supplies (recap) ==="
sed -n '/qcom,icnss@C800000 {/,/};/p' "$V" | grep -E "supply|config" | head -8

echo
echo "=== OUR dts: wifi node supplies ==="
python3 - <<'PYEOF'
import re
t = open('/mnt/d/TB331FCLinux/build/CANONICAL.dts', encoding='utf-8').read()
i = t.find('wifi@c800000 {')
if i < 0:
    i = t.find('wlan@c800000 {')
if i < 0:
    print('wifi node not found'); raise SystemExit
j = t.index('{', i); d = 0; k = j
while k < len(t):
    d += t[k] == '{'; d -= t[k] == '}'
    if d == 0 and k > j: break
    k += 1
print(t[i:k+1][:1200])
PYEOF
