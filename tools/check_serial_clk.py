with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

# in vendor.dts:
# clocks = <0x81 0x62>;
# In canonical dts:
# clocks = <0x02 0x6f>;
print("Check clocks in canonical DTS:")
pos = dts.find("serial@4a8c000")
print(dts[pos:pos+300])
