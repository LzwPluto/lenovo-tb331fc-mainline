with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

pos = dts.find("serial@4a8c000")
if pos != -1:
    end = dts.find("};", pos)
    print(dts[pos:end+2])
