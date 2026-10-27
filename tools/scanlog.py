#!/usr/bin/env python3
"""Scan a raw partition dump for bootloader / kernel log text."""
import re, sys, os

KEYS = re.compile(
    rb'LinuxLoader|BootLinux|UpdateDeviceTree|Dtbo|DTB|Splash|splash|ufdt|'
    rb'ERROR|FAIL|Booting|slot|kernel|cmdline|fdt|avb|ABL|LoadImage|'
    rb'Linux version|Kernel panic|dtb|UEFI|ExitBoot', re.I)


def scan(path, maxhits=40):
    d = open(path, 'rb').read()
    nz64 = sum(1 for i in range(0, len(d), 65536) if any(d[i:i + 65536]))
    print(f'===== {os.path.basename(path)}  size={len(d)}  nonzero64k={nz64}')
    print(f'   head : {d[:64].hex()}')
    # locate the last non-zero byte to judge how full it is
    last = 0
    for i in range(len(d) - 1, -1, -1):
        if d[i]:
            last = i
            break
    print(f'   last non-zero byte at 0x{last:x} ({last/len(d)*100:.1f}%)')
    runs = re.findall(rb'[\x20-\x7e\n\r\t]{8,}', d)
    print(f'   ascii runs: {len(runs)}')
    hits = [r for r in runs if KEYS.search(r)]
    print(f'   keyword hits: {len(hits)}')
    seen = set()
    shown = 0
    for r in hits:
        s = r.strip()
        if s in seen:
            continue
        seen.add(s)
        print('     ' + r[:150].decode('ascii', 'replace'))
        shown += 1
        if shown >= maxhits:
            break
    print()


for p in sys.argv[1:]:
    scan(p)
