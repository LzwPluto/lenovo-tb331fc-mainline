with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

for ph in ["0x5f", "0x60"]:
    pos = dts.find(f"phandle = <{ph}>;")
    if pos != -1:
        start = dts.rfind('\n\t\t\t', 0, pos)
        end = dts.find('};', pos) + 2
        print(f"Full node for {ph}:")
        print(dts[pos-100:pos+150])
