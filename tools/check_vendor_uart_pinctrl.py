with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

import re
matches = re.finditer(r'([a-zA-Z0-9_\-]+)\s*\{[^}]*pins\s*=\s*"gpio10"[^}]*\}', dts)
for m in matches:
    print("Match in vendor.dts:")
    print(m.group(0))

# Or check what phandles 0x107, 0x108, 0x109, 0x10a point to in vendor.dts
for ph in ["0x107", "0x108", "0x109", "0x10a", "0x10b", "0x10c", "0x10d", "0x10e"]:
    pos = dts.find(f"phandle = <{ph}>;")
    if pos != -1:
        start = dts.rfind('\n\t\t\t', 0, pos)
        end = dts.find('};', pos) + 2
        print(f"phandle {ph}:", dts[start:end].strip())
