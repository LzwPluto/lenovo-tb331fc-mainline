with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

pos = dts.find("phandle = <0x57>;")
if pos != -1:
    start = dts.rfind('\n\t\t\t', 0, pos)
    end = dts.find('};', pos)
    end2 = dts.find('};', end + 1)
    print(dts[start:end2+4])
