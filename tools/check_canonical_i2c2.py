with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

pos = dts.find("4a94000")
if pos != -1:
    end = dts.find("};", pos)
    print("Found 4a94000:")
    print(dts[pos:end+2])
else:
    print("4a94000 not found in canonical DTS")
