path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\arch\arm64\boot\dts\qcom\qrb4210-rb2.dts"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

idx = c.find("wcn3990-bt")
if idx != -1:
    start = c.rfind('{', 0, idx)
    end = c.find('};', idx)
    print("qrb4210-rb2.dts bluetooth:")
    print(c[start-10:end+2])
else:
    print("Not found in qrb4210-rb2.dts")
