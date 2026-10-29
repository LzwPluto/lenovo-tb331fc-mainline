import os

readme_content = """# Mainline Linux for Lenovo Xiaoxin Pad 2024 (`TB331FC` / `p255`)

[![Kernel Version](https://img.shields.io/badge/Linux-6.14.0--rc5--next-blue.svg)](https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git)
[![Status](https://img.shields.io/badge/Status-Display%20%7C%20Touch%20%7C%20GPU%20%7C%20Battery%20%7C%20WiFi%20Working-success.svg)]()
[![Platform](https://img.shields.io/badge/SoC-Qualcomm%20Snapdragon%20685%20(SM6225--AD)-orange.svg)]()

This repository contains the mainline Linux kernel source tree ported for the **Lenovo Xiaoxin Pad 2024** (PRC model: `TB331FC`, codename `p255`).

---

## 1. Hardware Specifications

| Component | Hardware Details |
| :--- | :--- |
| **SoC** | Qualcomm Snapdragon 685 4G (`SM6225-AD`, `khaje`), 4x Cortex-A73 @ 2.8GHz + 4x Cortex-A53 @ 1.9GHz |
| **GPU** | Adreno 610 (`a610`, Freedreno DRM driver) |
| **Display** | 11.0" 1920x1200 IPS LCD (Himax `HX83102`, `p255-inx`), VESA DSC compression, 60Hz/90Hz |
| **Backlight** | Kinetic Technologies `KTZ8866` (I2C0 @ `0x11`) |
| **Touchscreen** | Novatek `NVT-TS` capacitive digitizer (SPI0 @ `spi@4a80000`, cs0) |
| **Battery / PMIC** | Mitsumi `MM8013` fuel gauge (I2C1 @ `0x55`), PM6125 SPMI PMIC |
| **Connectivity** | Qualcomm Cherokee `WCN3990` (Wi-Fi: `ath10k_snoc`, Bluetooth: UART @ `serial@4a8c000`) |
| **Audio** | 4x Awinic `AW88166` Smart PAs (I2C0 @ `0x34`, `0x35`; I2C1 @ `0x34`, `0x35`), LPASS MI2S DAI |
| **Storage / RAM** | 6GB / 8GB LPDDR4x, 128GB UFS 2.2 |

---

## 2. Hardware Support Status

| Subsystem | Driver / Status | Notes |
| :--- | :---: | :--- |
| **Display** | ✅ Working | Himax `HX83102` DSI panel with VESA DSC 1.1 (`slice_per_pkt = 2`) |
| **Backlight** | ✅ Working | Kinetic `KTZ8866` driver with GNOME UI brightness control & blank power-off |
| **GPU 3D Accel** | ✅ Working | Mesa Freedreno (`a610`), Wayland GNOME Shell hardware acceleration |
| **Touchscreen** | ✅ Working | Novatek NVT capacitive touch with SPI recovery & heartbeat |
| **Battery Gauge** | ✅ Working | Mitsumi `MM8013` reports capacity (%), voltage, current, temperature |
| **Wi-Fi** | ✅ Working | Qualcomm `WCN3990` (`ath10k_snoc`) connected to WPA2/WPA3 hotspot |
| **Power Management** | ✅ Working | `s2idle` (Suspend-to-Idle / Freeze) low power state |
| **Hardware Keys** | ✅ Working | Power key (`pm8941_pwrkey`), Volume Down (`pm8941_resin`), Volume Up (`gpio-keys`), Hall sensor |
| **Audio** | 🟡 In Progress | 4x `AW88166` Smart PA driver integrated; awaiting sound card DAI Devicetree binding |
| **Bluetooth** | 🟡 In Progress | WCN3990 UART registered; suspend timeout fixed; firmware baud sync tuning |

---

## 3. How to Build the Kernel

### Prerequisites (Ubuntu / Debian / WSL)
```bash
sudo apt update
sudo apt install -y build-essential gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
    bison flex libssl-dev libelf-dev bc git device-tree-compiler
```

### 1. Configure
```bash
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

make tb331fc_defconfig
```

### 2. Compile Kernel & Devicetrees
```bash
make -j$(nproc) Image.gz qcom/sm6225-lenovo-tb331fc.dtb
```

### 3. Output Artifacts
* Kernel Image: `arch/arm64/boot/Image.gz`
* Devicetree Blob (DTB): `arch/arm64/boot/dts/qcom/sm6225-lenovo-tb331fc.dtb`

---

## 4. Boot Packaging & Flashing (Slot B Safety Rule)

> [!WARNING]
> **NEVER flash Slot A.** Slot A holds the factory Android / HyperOS recovery system. Always flash to Slot B (`boot_b`, `vendor_boot_b`).

### Package `boot_b.img`
```bash
mkbootimg \
  --kernel arch/arm64/boot/Image.gz \
  --header_version 3 \
  --pagesize 4096 \
  --os_version 14.0.0 \
  --os_patch_level 2026-03 \
  --output boot.img
```

### Flash to Slot B via Fastboot
```bash
fastboot flash boot_b boot.img
fastboot flash vendor_boot_b vendor_boot.img
fastboot --set-active=b
fastboot reboot
```

---

## 5. Contributing / Help Wanted

We are actively seeking contributions from the Qualcomm Linux and postmarketOS community! Key areas where help is needed:
1. **ALSA Audio Sound Card**: Completing the machine driver / devicetree DAI link connecting Qualcomm LPASS MI2S to the 4x Awinic `AW88166` amplifiers. Audio firmware dump and XML mixer paths from factory Android are available.
2. **Bluetooth Initialization**: Tuning the CTS/RTS timing and baud sequence for WCN3990 firmware loading on UART.
3. **Power Button Instant Sleep**: Tuning GNOME Wayland desktop power-key hooks.

Feel free to open Issues or pull requests!
"""

target = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/README.md'
open(target, 'w').write(readme_content)
print(f"Wrote {target} successfully ({len(readme_content)} bytes)")
