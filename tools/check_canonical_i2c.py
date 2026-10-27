with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

for bus in ["4a84000", "4a88000"]:
    pos = dts.find(f"i2c@{bus}")
    if pos != -1:
        end = dts.find("};", pos)
        print(f"=== i2c@{bus} ===")
        print(dts[pos:end+2])
