#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1

dtc -@ -I dts -O dtb -o CANONICAL_ktz.dtb CANONICAL_383_dma.dts > /tmp/dtc.log 2>&1
echo "dtc exit=$?"
echo -n "ERROR lines: "
grep -c "ERROR" /tmp/dtc.log
ls -l CANONICAL_ktz.dtb || exit 1

python3 - <<'PYEOF'
d = open('/mnt/d/TB331FCLinux/build/CANONICAL_ktz.dtb', 'rb').read()
for k in [b'kinetic,ktz8866', b'bl_vddpos', b'bl_vddneg', b'__symbols__', b'383000000']:
    print('%-16s -> %s' % (k.decode(), 'YES' if k in d else 'no'))
print('size', len(d))
PYEOF
