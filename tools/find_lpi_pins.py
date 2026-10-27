with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

import re
for ph in ["0x26d", "0x26e", "0x26f", "0x270", "0x271", "0x272", "0x273", "0x274"]:
    pos = dts.find(f"phandle = <{ph}>;")
    if pos != -1:
        start = dts.rfind('\t\t', 0, pos)
        end = dts.find('};', pos) + 2
        print(f"Node for {ph}:", dts[start:end].strip())
