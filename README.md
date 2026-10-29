# Lenovo Xiaoxin Pad 2024 (`TB331FC` / `p255`) Mainline Linux Port

[![Platform](https://img.shields.io/badge/SoC-Qualcomm%20Snapdragon%20685%20(SM6225--AD)-orange.svg)]()
[![Kernel](https://img.shields.io/badge/Kernel-6.14.0--rc5--next-blue.svg)]()
[![Status](https://img.shields.io/badge/Status-Display%20%7C%20Touch%20%7C%20GPU%20%7C%20WiFi%20%7C%20Battery%20Working-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-GPLv2%20%2F%20MIT-lightgrey.svg)]()

This repository contains the complete tooling, canonical Devicetrees, reverse-engineered hardware documentation, extracted factory firmware, and boot packaging scripts for running **Mainline Linux (kernel 6.14+)** on the **Lenovo Xiaoxin Pad 2024** (`TB331FC`, codename `p255`).

> **Associated Kernel Repository**: [linux-lenovo-tb331fc](https://github.com/) (Contains full kernel source tree, ported drivers, defconfig, and in-tree devicetrees).

---

## 1. Hardware Overview

| Component | Hardware Details | Linux Driver / Subsystem |
| :--- | :--- | :--- |
| **SoC** | Qualcomm Snapdragon 685 4G (`SM6225-AD`, `khaje`) | Qualcomm SoC platform |
| **CPU** | 4x Kryo 265 Gold (Cortex-A73 @ 2.8GHz) + 4x Kryo 265 Silver (Cortex-A53 @ 1.9GHz) | `arm64` SMP |
| **GPU** | Adreno 610 (`a610`) | Mesa Freedreno (`kgsl` / DRM MSM) |
| **Display Panel** | 11.0" 1920x1200 IPS LCD, 60Hz / 90Hz (`lenovo,p255-inx`) | Himax `HX83102` DSI panel + VESA DSC 1.1 |
| **Backlight** | Kinetic Technologies `KTZ8866` (I2C0 @ `0x11`) | `ktz8866` Backlight Driver |
| **Touchscreen** | Novatek `NT36523N` 10-point capacitive digitizer (SPI0 CS1) | `novatek-nvt-ts` SPI Touch driver |
| **Battery / Fuel Gauge** | Mitsumi `MM8013` (I2C1 @ `0x55`) | `mm8013` Power Supply Driver |
| **PMIC / PON Keys** | Qualcomm `PM6125` SPMI PMIC | `pm8941_pwrkey` / `pm8941_resin` |
| **Wi-Fi** | Qualcomm Cherokee `WCN3990` | `ath10k_snoc` (WLAN) |
| **Bluetooth** | Qualcomm Cherokee `WCN3990` (UART @ `serial@4a8c000`) | `hci_uart_qca` (Bluetooth) |
| **Audio Smart PA** | 4x Awinic `AW88166` (I2C0 @ `0x34`,`0x35`; I2C1 @ `0x34`,`0x35`) | Awinic `AW88166` ALSA SoC Codec |

---

## 2. Hardware Support Status

| Subsystem | Status | Implementation Details |
| :--- | :---: | :--- |
| **Display Panel** | ✅ **Working** | 1200x1920 @ 90Hz native portrait mode, VESA DSC 1.1 with `slice_per_pkt = 2`. Zero tearing. |
| **Backlight Control** | ✅ **Working** | Kinetic `KTZ8866` I2C driver. GNOME UI slider works smoothly; backlight powers down completely to 0 mA on screen blank. |
| **GPU 3D Acceleration** | ✅ **Working** | Adreno 610 driven by Freedreno. Wayland (GNOME Shell / Niri) running with hardware acceleration. |
| **Touchscreen** | ✅ **Working** | Novatek `NT36523N` with automatic recovery and heartbeat, 10-point multi-touch. |
| **Battery Reporting** | ✅ **Working** | Mitsumi `MM8013` reporting percentage (%), voltage (mV), current (mA), temperature, and health state. |
| **Wi-Fi** | ✅ **Working** | Qualcomm WCN3990 connected to local hotspots via `ath10k_snoc`. |
| **Low Power Sleep** | ✅ **Working** | `s2idle` (Suspend-to-Idle / Freeze) mode supported. Wakes up reliably via Power button. |
| **Hardware Keys** | ✅ **Working** | Power key (`pm8941_pwrkey`), Volume Down (`pm8941_resin`), Volume Up (`gpio-keys`), Hall magnetic sensor. |
| **Audio** | 🟡 **In Progress** | 4x `AW88166` Smart PA drivers implemented in kernel. Needs LPASS MI2S DAI sound card Devicetree binding and UCM2/PipeWire profile. |
| **Bluetooth** | 🟡 **In Progress** | UART node registered, suspend hang fixed in `hci_qca.c`. Tuning WCN3990 firmware baud rate handshake. |

---

## 3. Repository Structure

```text
├── docs/                      # Comprehensive technical guides and hardware documentation
│   ├── TB331FC-FULL-PORT-GUIDE.md  # Complete step-by-step porting guide & UFS partition table
│   ├── WORKING-BOOT-RECIPE.md      # Detailed boot recipes, clocks, and ABL symbols guide
│   └── HANDOVER.md                 # Daily developer handover logs and milestones
├── build/                     # Canonical Devicetree sources and packaging tools
│   ├── CANONICAL_383_dma.dts       # Verified working canonical Devicetree for TB331FC
│   └── mkbootimg / repack scripts # Scripts to build boot.img and vendor_boot.img
├── dump/                      # Hardware assets extracted from factory HyperOS
│   └── android_pulled_assets/
│       ├── audio_fw/          # aw883xx_acf.bin, calibration data, and XML mixer paths
│       ├── bt_firmware/       # Qualcomm WCN3990 Cherokee firmware (crbtfw21.tlv, crnv21.bin)
│       └── android_live_dt_base.tar.gz  # Full official Android devicetree dump (11,429 nodes)
├── tools/                     # Automation, testing, and flashing scripts
│   ├── alpine.ps1             # Windows USB gadget serial interactive console
│   ├── ssh_exec.py            # High-speed remote SSH runner over Wi-Fi
│   └── repack_vb_dtb2.py      # Automated vendor_boot DTB repacker
└── ref/                       # Vendor touchscreen drivers and disassembly references
```

---

## 4. Safety First: The Slot B Rule

> [!WARNING]
> **NEVER write, flash, or erase Slot A partitions (`boot_a`, `vendor_boot_a`).**
> Slot A contains the untampered factory Android / HyperOS recovery image. Always target Slot B:
> ```bash
> fastboot flash boot_b boot.img
> fastboot flash vendor_boot_b vendor_boot.img
> fastboot --set-active=b
> fastboot reboot
> ```

---

## 5. Call for Collaboration (Help Wanted!)

Porting an entire modern Qualcomm tablet is a huge endeavor, and we welcome anyone in the open source, postmarketOS, and Linux on Qualcomm communities to join!

### Areas needing collaboration:
1. **ALSA Audio / Sound Card DAI Links**:
   * We have extracted all official audio calibration files (`aw883xx_acf.bin`, `spk_cal_f`, `spk_cal_r`, and `mixer_paths_bengal_idp.xml`).
   * The kernel driver `aw88166.c` is ready. We need help creating the sound card machine driver / DTS binding to route LPASS MI2S DAI to the 4 Smart PAs.
2. **Qualcomm WCN3990 Bluetooth Firmware Sync**:
   * The Bluetooth chip powers on and receives UART commands, but occasionally encounters a handshake timeout during baud switch.
3. **GNOME Power Key Hook**:
   * Enabling seamless short-press screen toggle directly from desktop sessions.

---

## 6. License & Acknowledgements

* Kernel modifications and device drivers: GPLv2.
* Tooling, documentation, and scripts: MIT.
* Acknowledgements to the `linux-sm6225` and postmarketOS developers whose earlier work on TB128FU provided invaluable references.
