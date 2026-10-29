with open(r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

idx = dts.find("wcn3990-bt")
if idx != -1:
    start = dts.rfind('{', 0, idx)
    end = dts.find('};', idx)
    print("Bluetooth node in canonical DTS:")
    print(dts[start-20:end+2])
