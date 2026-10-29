with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

pos = dts.find("qcom,power-on@800")
if pos == -1:
    pos = dts.find("pon@800")
if pos != -1:
    end = dts.find("};", pos + 300)
    print("vendor.dts pon block:")
    print(dts[pos:end+2])
else:
    print("pon block not found in vendor.dts")
