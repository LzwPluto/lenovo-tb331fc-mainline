with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

idx = dts.find('compatible = "qcom,bengal-asoc-snd";')
if idx != -1:
    start = dts.rfind('{', 0, idx)
    # count braces
    depth = 1
    end = start + 1
    while depth > 0 and end < len(dts):
        if dts[end] == '{':
            depth += 1
        elif dts[end] == '}':
            depth -= 1
        end += 1
    print("Full Sound Node:")
    print(dts[start-20:end])
else:
    print("Sound node not found!")
