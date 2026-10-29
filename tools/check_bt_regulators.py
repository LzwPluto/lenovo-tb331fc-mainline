with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

for ph in ["0x4c", "0x59", "0xa8", "0xa9"]:
    pos = dts.find(f"phandle = <{ph}>;")
    if pos != -1:
        start = dts.rfind('\n', 0, pos)
        line_start = dts.rfind('\n\t', 0, pos-20)
        end = dts.find('};', pos) + 2
        print(f"phandle {ph}:", dts[line_start:end].strip()[:200])
