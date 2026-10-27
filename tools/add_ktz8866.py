#!/usr/bin/env python3
"""add_ktz8866.py

The backlight of TB331FC is NOT the panel's DCS 0x51 path -- it is a separate
Kinetic KTZ8866 LED driver on I2C:

    Android: [ktz8866_leds] bkl_probe: probe success
             hwen_gpio --<425>          -> TLMM GPIO 425-398 = 27
             bkl_brightness_set: backlight brightness is 0x403
    vendor DT (ov2.dts fragment@43): bkl-bl@11 { reg = <0x11>; bkl,hwen-gpio = <&tlmm 0x1b 0>; }
    Android sysfs: /sys/bus/i2c/devices/0-0011 ->
                   4ac0000.qupv3_0_geni_se/4a84000.i2c/i2c-0/0-0011

Mainline has drivers/video/backlight/ktz8866.c (CONFIG_BACKLIGHT_KTZ8866),
compatible "kinetic,ktz8866", and it requires vddpos-supply, vddneg-supply and
enable-gpios.

This script:
  1. adds two always-on regulator-fixed nodes to feed vddpos/vddneg (Android's
     DT does not model them either -- the rails are always up);
  2. adds the ktz8866 node to i2c@4a84000 (address 0x11, enable GPIO 27);
  3. sets .has_dcs_backlight = false for the p255_inx panel desc, because the
     DCS 0x51 writes go nowhere on this TDDI and only collide with the 90 Hz
     DSC video stream (dsi_err_worker status=5).
"""
import re
import sys

DTS = '/mnt/d/TB331FCLinux/build/CANONICAL_383_dma.dts'
PANEL = ('/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/'
         'drivers/gpu/drm/panel/panel-himax-hx83102.c')

s = open(DTS, encoding='utf-8').read()
if 'kinetic,ktz8866' in s:
    print('DT already has ktz8866')
else:
    # ---- pick fresh phandles ----
    used = [int(m, 16) for m in re.findall(r'phandle = <0x([0-9a-f]+)>', s)]
    p1, p2 = max(used) + 1, max(used) + 2
    print('max phandle 0x%x -> new 0x%x, 0x%x' % (max(used), p1, p2))

    # ---- 1. fixed regulators, siblings of vbus_p1 ----
    anchor = """		regulator-min-microvolt = <0x4c4b40>;
		regulator-max-microvolt = <0x4c4b40>;
		gpio = <0x28 0x48 0x00>;
		enable-active-high;
		status = "okay";
	};"""
    regs = anchor + """

	bl_vddpos: regulator-bl-vddpos {
		compatible = "regulator-fixed";
		regulator-name = "bl_vddpos";
		regulator-min-microvolt = <0x53ec60>;
		regulator-max-microvolt = <0x53ec60>;
		regulator-always-on;
		phandle = <0x%x>;
	};

	bl_vddneg: regulator-bl-vddneg {
		compatible = "regulator-fixed";
		regulator-name = "bl_vddneg";
		regulator-min-microvolt = <0x53ec60>;
		regulator-max-microvolt = <0x53ec60>;
		regulator-always-on;
		phandle = <0x%x>;
	};""" % (p1, p2)

    if anchor not in s:
        sys.exit('vbus_p1 anchor not found')
    s = s.replace(anchor, regs, 1)
    print('added bl_vddpos / bl_vddneg fixed regulators')

    # ---- 2. ktz8866 on i2c@4a84000 ----
    i2c_anchor = """				dmas = <0x46 0x00 0x01 0x03 0x46 0x01 0x01 0x03>;
				dma-names = "tx\\0rx";
				#address-cells = <0x01>;
				#size-cells = <0x00>;
				status = "okay";"""
    ktz = i2c_anchor + """

				backlight@11 {
					compatible = "kinetic,ktz8866";
					reg = <0x11>;
					enable-gpios = <0x28 0x1b 0x00>;
					vddpos-supply = <0x%x>;
					vddneg-supply = <0x%x>;
					current-num-sinks = <0x06>;
					kinetic,current-ramp-delay-ms = <0x80>;
					kinetic,led-enable-ramp-delay-ms = <0x01>;
				};""" % (p1, p2)

    if i2c_anchor not in s:
        sys.exit('i2c@4a84000 anchor not found')
    s = s.replace(i2c_anchor, ktz, 1)
    print('added ktz8866@0x11 on i2c@4a84000 (enable GPIO 27)')

    open(DTS, 'w', encoding='utf-8', newline='\n').write(s)

# ---- 3. panel: drop the DCS backlight for this panel ----
p = open(PANEL, encoding='utf-8').read()
OLD_DESC = """	.has_dcs_backlight = true,
	.inverted_dbv = true,
	.has_dsc = true,
	.init = lenovo_p255_inx_init,"""
NEW_DESC = """	/* the LEDs are driven by a KTZ8866 on I2C, not by DCS 0x51 */
	.has_dcs_backlight = false,
	.inverted_dbv = true,
	.has_dsc = true,
	.init = lenovo_p255_inx_init,"""
if NEW_DESC in p:
    print('panel: has_dcs_backlight already false')
elif OLD_DESC in p:
    p = p.replace(OLD_DESC, NEW_DESC, 1)
    open(PANEL, 'w', encoding='utf-8', newline='\n').write(p)
    print('panel: has_dcs_backlight -> false (KTZ8866 drives the LEDs)')
else:
    print('WARNING: lenovo_p255_inx_desc block not recognised')
