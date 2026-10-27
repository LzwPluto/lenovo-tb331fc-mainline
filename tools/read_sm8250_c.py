path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\qcom\sm8250.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
funcs = re.findall(r'static[^\n]+probe[^\n]+', text)
print("Probe functions:", funcs)

idx = text.find("qcom,sm8250-sndcard")
print("Around qcom,sm8250-sndcard:")
print(text[idx-200:idx+300])
