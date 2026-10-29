path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\power\reset\qcom-pon.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

print("qcom-pon.c probe:")
idx = text.find("pm8916_pon_probe")
if idx == -1:
    idx = text.find("probe")
print(text[idx-50:idx+600])
