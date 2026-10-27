with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

import re
matches = re.finditer(r'([a-zA-Z0-9_\-]+)\s*\{[^}]*phandle\s*=\s*<0x32f>[^}]*\}', dts)
for m in matches:
    print("phandle 0x32f:", m.group(0))

# Or search around phandle = <0x32f>
pos = dts.find("phandle = <0x32f>;")
if pos != -1:
    print(dts[pos-200:pos+300])
