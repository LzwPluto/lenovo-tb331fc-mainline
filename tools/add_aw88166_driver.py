#!/usr/bin/env python3
"""add_aw88166_driver.py

Integrates the Awinic AW88166 Smart PA codec driver into sound/soc/codecs:
- Updates Kconfig
- Updates Makefile
- Enables CONFIG_SND_SOC_AW88166=m in .config and tb331fc_defconfig
"""
import sys

base = "/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port"
kcfg_path = f"{base}/sound/soc/codecs/Kconfig"
mk_path = f"{base}/sound/soc/codecs/Makefile"
dotconfig_path = f"{base}/.config"
defconfig_path = f"{base}/arch/arm64/configs/tb331fc_defconfig"

# 1. Update Kconfig
with open(kcfg_path, "r", encoding="utf-8") as f:
    kcfg = f.read()

if "config SND_SOC_AW88166" not in kcfg:
    entry = """
config SND_SOC_AW88166
\ttristate "Soc Audio for awinic aw88166"
\tdepends on I2C
\tselect CRC32
\tselect REGMAP_I2C
\tselect GPIOLIB
\tselect SND_SOC_AW88395_LIB
\thelp
\t  This option enables support for aw88166 Smart PA.
\t  The Awinic AW88166 is an I2S/TDM input, high efficiency
\t  digital Smart K audio amplifier.
"""
    kcfg += entry
    with open(kcfg_path, "w", encoding="utf-8") as f:
        f.write(kcfg)
    print("Updated sound/soc/codecs/Kconfig")

# 2. Update Makefile
with open(mk_path, "r", encoding="utf-8") as f:
    mk = f.read()

if "snd-soc-aw88166" not in mk:
    mk += "\nsnd-soc-aw88166-y := aw88166.o\nobj-$(CONFIG_SND_SOC_AW88166) += snd-soc-aw88166.o\n"
    with open(mk_path, "w", encoding="utf-8") as f:
        f.write(mk)
    print("Updated sound/soc/codecs/Makefile")

# 3. Update .config and defconfig
for cpath in [dotconfig_path, defconfig_path]:
    try:
        with open(cpath, "r", encoding="utf-8") as f:
            cfg = f.read()
        if "CONFIG_SND_SOC_AW88166" not in cfg:
            cfg += "\nCONFIG_SND_SOC_AW88166=m\nCONFIG_SND_SOC_AW88395_LIB=m\n"
            with open(cpath, "w", encoding="utf-8") as f:
                f.write(cfg)
            print(f"Updated {cpath}")
    except Exception as e:
        print(f"Could not update {cpath}: {e}")

print("AW88166 integration completed successfully!")
