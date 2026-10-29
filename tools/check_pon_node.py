with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

import re
matches = [l.strip() for l in dts.splitlines() if any(k in l.lower() for k in ['pwrkey', 'resin', 'pon@800', 'pm8941-pwrkey', 'qcom,pm8998-pon'])]
print("Matches in canonical DTS:")
for m in matches:
    print("  ", m)

pos = dts.find("@800")
while pos != -1:
    print("--- @800 block ---")
    print(dts[pos-50:pos+300])
    pos = dts.find("@800", pos + 1)
