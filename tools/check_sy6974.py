with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

import re
matches = [l.strip() for l in dts.splitlines() if 'sy6974' in l.lower()]
print("sy6974 matches:", matches)

pos = dts.find("sy6974")
while pos != -1:
    print("---")
    print(dts[pos-100:pos+200])
    pos = dts.find("sy6974", pos + 1)
