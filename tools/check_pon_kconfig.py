path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\power\reset\Kconfig"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("config POWER_RESET_QCOM_PON")
print(text[idx:idx+400])
