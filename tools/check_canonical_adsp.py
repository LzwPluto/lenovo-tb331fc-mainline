with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

import re
matches = re.finditer(r'([a-zA-Z0-9_\-]+@[0-9a-fA-F]+\s*\{[^}]*compatible\s*=\s*"[^"]*(?:adsp|pas|cdsp|q6)[^"]*"[^}]*\})', dts)
for m in matches:
    print("--- Found ---")
    print(m.group(0)[:400])

remotes = [l.strip() for l in dts.splitlines() if 'remoteproc' in l.lower() or 'adsp' in l.lower()]
print(f"Total lines mentioning remoteproc/adsp in canonical DTS: {len(remotes)}")
for l in remotes[:15]:
    print("  ", l)
