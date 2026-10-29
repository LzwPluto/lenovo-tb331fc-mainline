import re

config_path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\.config"
with open(config_path, "r", encoding="utf-8") as f:
    text = f.read()

# Enable QCOM_PON and REBOOT_MODE as builtin (=y)
text = re.sub(r'CONFIG_POWER_RESET_QCOM_PON=m', 'CONFIG_POWER_RESET_QCOM_PON=y', text)
text = re.sub(r'CONFIG_REBOOT_MODE=m', 'CONFIG_REBOOT_MODE=y', text)
text = re.sub(r'CONFIG_LOCALVERSION_AUTO=y', '# CONFIG_LOCALVERSION_AUTO is not set', text)

with open(config_path, "w", encoding="utf-8") as f:
    f.write(text)

# Also update tb331fc_defconfig
defconfig_path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\arch\arm64\configs\tb331fc_defconfig"
with open(defconfig_path, "r", encoding="utf-8") as f:
    defcfg = f.read()

if "CONFIG_POWER_RESET_QCOM_PON=y" not in defcfg:
    defcfg += "\nCONFIG_POWER_RESET_QCOM_PON=y\nCONFIG_REBOOT_MODE=y\n# CONFIG_LOCALVERSION_AUTO is not set\n"
    with open(defconfig_path, "w", encoding="utf-8") as f:
        f.write(defcfg)

print("Updated kernel configs!")
