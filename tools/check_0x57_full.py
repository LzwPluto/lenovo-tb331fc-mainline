with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

pos = dts.find("phandle = <0x57>;")
print(dts[pos-50:pos+600])
