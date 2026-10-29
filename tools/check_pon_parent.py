with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

pos = dts.find("pon@800")
if pos != -1:
    parent_pos = dts.rfind('{', 0, pos)
    parent_line = dts.rfind('\n', 0, parent_pos)
    print("Parent line:", dts[parent_line:parent_pos+1])
    # print 500 chars before pos
    print(dts[pos-400:pos+300])
