with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

pos = dts.find('rt1711h@4e')
if pos != -1:
    end = dts.find('};', pos)
    print(dts[pos:end+2])
