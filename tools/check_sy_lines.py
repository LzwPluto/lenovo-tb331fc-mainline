with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8") as f:
    dts = f.read()

import re
matches = [l.strip() for l in dts.splitlines() if 'sy6974' in l.lower()]
print("sy6974 lines remaining:", matches)
