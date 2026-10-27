#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== LDO/SMPS entries inside our regulators-0 ==="
awk '/regulators-0 \{/,/^\t\t\t\t\};/' "$C" | grep -E "^\t+\t+(s[0-9]+|l[0-9]+|bob) \{" | sed 's/[[:space:]]*{//' | tr -d '\t' | tr '\n' ' '
echo
echo
echo "=== which of the four we need are present? ==="
for r in l9 l16 l17 l23; do
    if awk '/regulators-0 \{/,/^\t\t\t\t\};/' "$C" | grep -qE "^\t+\t+$r \{"; then
        echo "  $r : PRESENT"
    else
        echo "  $r : MISSING  <-- needs to be added"
    fi
done
echo
echo "=== our regulators-0 phandles (to pick free numbers) ==="
awk '/regulators-0 \{/,/^\t\t\t\t\};/' "$C" | grep -oE "phandle = <0x[0-9a-f]+>" | tail -6
echo "highest phandle in whole file: $(grep -oE 'phandle = <0x[0-9a-f]+>' "$C" | grep -oE '0x[0-9a-f]+' | sort -u | tail -1)"
