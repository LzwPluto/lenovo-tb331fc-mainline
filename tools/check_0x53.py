with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8") as f:
    dts = f.read()

import re
matches = [l.strip() for l in dts.splitlines() if '0x53' in l]
print("0x53 occurrences:", matches)
