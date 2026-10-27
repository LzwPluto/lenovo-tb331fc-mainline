import re

with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Also let's inspect android dmesg or platform-names to see what drivers bound to these
addresses = ['08', '09', '11', '28', '34', '35', '42', '6b', '55', '22', '4e']
for addr in addresses:
    print(f"===================== Matches for @{addr} =====================")
    # Search for node declaration like xxx@addr { ... }
    matches = re.finditer(rf'([a-zA-Z0-9_\-]+@{addr}\s*\{{[^}}]*\}})', text)
    found = False
    for m in matches:
        found = True
        print(m.group(1)[:400])
        print("----------------------------------------------------------------")
    if not found:
        # Search for reg = <0xaddr>
        reg_matches = re.finditer(rf'([a-zA-Z0-9_\-]+\s*\{{[^}}]*reg\s*=\s*<0x{addr}>[^}}]*\}})', text, re.IGNORECASE)
        for rm in reg_matches:
            found = True
            print(rm.group(1)[:400])
            print("----------------------------------------------------------------")
    if not found:
        print(f"No direct match in vendor.dts for {addr}")
