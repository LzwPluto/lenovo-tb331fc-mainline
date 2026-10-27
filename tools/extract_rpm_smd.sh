#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
OUT=/mnt/d/TB331FCLinux/ref/android/rpm_smd_block.dts

# find the "qcom,rpm-smd {" node and its matching closing brace
start=$(grep -n "qcom,rpm-smd {" "$V" | head -1 | cut -d: -f1)
echo "node starts at line $start"
python3 - "$V" "$OUT" "$start" <<'PYEOF'
import sys
src, out, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
lines = open(src, encoding='utf-8').read().split('\n')
i = start - 1
depth = 0
j = i
while j < len(lines):
    depth += lines[j].count('{') - lines[j].count('}')
    if depth == 0 and j > i:
        break
    j += 1
block = '\n'.join(lines[i:j+1])
open(out, 'w', encoding='utf-8', newline='\n').write(block)
print(f'extracted {j-i+1} lines -> {out}')
PYEOF

echo
echo "=== block head ==="
head -20 "$OUT"
echo
echo "=== counts inside the block ==="
echo "  phandle assignments : $(grep -c 'phandle = <' "$OUT")"
echo "  regulator nodes     : $(grep -c 'compatible = "qcom,rpm-smd-regulator"' "$OUT")"
echo "  resource nodes      : $(grep -c 'qcom,rpm-smd-regulator-resource' "$OUT")"
echo "  internal phandle refs: $(grep -oE '<0x[0-9a-f]+>' "$OUT" | wc -l)"
