path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\arch\arm64\boot\dts\qcom\qrb4210-rb2.dts"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

idx = c.find('compatible = "qcom,qrb4210-rb2-sndcard";')
start = c.rfind('sound {', 0, idx)
# find matching closing brace
depth = 0
for i in range(start, len(c)):
    if c[i] == '{':
        depth += 1
    elif c[i] == '}':
        depth -= 1
        if depth == 0:
            print(c[start:i+1])
            break
