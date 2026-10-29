path = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/arch/arm64/boot/dts/qcom/Makefile'
lines = [l for l in open(path).readlines() if 'tb331fc' not in l]
lines.append('dtb-$(CONFIG_ARCH_QCOM)\t+= sm6225-lenovo-tb331fc.dtb\n')
open(path, 'w').writelines(lines)
print('Updated Makefile cleanly!')
