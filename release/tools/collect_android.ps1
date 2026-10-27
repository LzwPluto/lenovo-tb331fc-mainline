# collect_android.sh - 一次性抓取 Android 侧所有可能有用的运行时数据
#
# 用法: powershell -File collect_android.ps1
# 输出: D:\TB331FCLinux\ref\android\dump-<timestamp>\
#
# 目标：拿到 WiFi / 蓝牙 / 触控 之后排查所需的全部证据，
#       避免反复切槽回来补抓。

$ErrorActionPreference = 'Continue'
$adb = 'D:\搞机助手\adb.exe'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$out = "D:\TB331FCLinux\ref\android\dump-$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Grab([string]$name, [string]$cmd) {
    $path = Join-Path $out $name
    try {
        $res = & $adb shell $cmd 2>$null
        if ($res) { $res | Out-File -FilePath $path -Encoding UTF8 }
        $n = if ($res) { $res.Count } else { 0 }
        Write-Host ("  {0,-34} {1,6} lines" -f $name, $n)
    } catch {
        Write-Host ("  {0,-34} FAILED" -f $name)
    }
}

function GrabFile([string]$name, [string]$remote) {
    $path = Join-Path $out $name
    & $adb pull $remote $path 2>$null | Out-Null
    if (Test-Path $path) {
        Write-Host ("  {0,-34} {1,6} KB" -f $name, [math]::Round((Get-Item $path).Length/1KB,1))
    } else {
        Write-Host ("  {0,-34} MISSING" -f $name)
    }
}

Write-Host '=== 等待设备 ==='
for ($i = 0; $i -lt 45; $i++) {
    if (& $adb devices 2>&1 | Select-String 'device$') { break }
    Start-Sleep -Seconds 2
}
& $adb devices

Write-Host '=== 尝试 root（成功的话 debugfs 全部可读）==='
& $adb root 2>&1 | Out-Null
Start-Sleep -Seconds 3
for ($i = 0; $i -lt 10; $i++) {
    if (& $adb devices 2>&1 | Select-String 'device$') { break }
    Start-Sleep -Seconds 2
}
& $adb shell id 2>$null

Write-Host '=== 1) 立即抓 dmesg（趁日志还在）==='
Grab 'dmesg-early.txt'  'dmesg'
Grab 'bootreason.txt'   'cat /proc/cmdline'

Write-Host '=== 2) GPIO / 引脚归属（找 WLAN/BT 使能脚的关键）==='
Grab 'debugfs-gpio.txt'      'cat /sys/kernel/debug/gpio'
Grab 'pinmux-pins.txt'       'cat /sys/kernel/debug/pinctrl/500000.pinctrl/pinmux-pins'
Grab 'pinmux-functions.txt'  'cat /sys/kernel/debug/pinctrl/500000.pinctrl/pinmux-functions'
Grab 'gpio-class.txt'        'ls -l /sys/class/gpio'
Grab 'gpiochips.txt'         'cat /sys/kernel/debug/gpio'

Write-Host '=== 3) 稳压器 / 时钟（供电与参考时钟真值）==='
Grab 'regulator-summary.txt' 'cat /sys/kernel/debug/regulator/regulator_summary'
Grab 'clk-summary.txt'       'cat /sys/kernel/debug/clk/clk_summary'
Grab 'regulator-state.txt'   'for d in /sys/class/regulator/*; do n=$(cat $d/name); echo "$n $(cat $d/microvolts) $(cat $d/state)"; done'

Write-Host '=== 4) 驱动绑定与设备 ==='
Grab 'spi-devices.txt'    'ls -l /sys/bus/spi/devices'
Grab 'i2c-devices.txt'    'ls -l /sys/bus/i2c/devices'
Grab 'platform-names.txt' 'ls /sys/bus/platform/devices'
Grab 'net.txt'            'ls -l /sys/class/net'
Grab 'modules.txt'        'cat /proc/modules'
Grab 'interrupts.txt'     'cat /proc/interrupts'
Grab 'iomem.txt'          'cat /proc/iomem'
Grab 'dma-buf.txt'        'cat /sys/kernel/debug/dma_buf/bufinfo'

Write-Host '=== 5) 蓝牙 / WiFi / 触控 专属 ==='
Grab 'bt-attrs.txt'        'ls -l /sys/class/bluetooth'
Grab 'bt-hci0.txt'         'for f in /sys/class/bluetooth/hci0/*; do echo "$f=$(cat $f 2>/dev/null)"; done'
Grab 'qca-serdev.txt'      'ls -l /sys/bus/serial/devices'
Grab 'wlan-debugfs.txt'    'ls -R /sys/kernel/debug/icnss 2>/dev/null'
Grab 'wlan-qmi.txt'        'ls -l /sys/kernel/debug/qmi 2>/dev/null'
Grab 'wlan-pdr.txt'        'ls -l /sys/bus/pdr/devices 2>/dev/null'
Grab 'nvt-sysfs.txt'       'find /sys -name "*nvt*" -o -name "*NVT*" 2>/dev/null | head -40'
Grab 'hxchipset-sysfs.txt' 'find /sys -name "*hxchipset*" -o -name "*himax*" 2>/dev/null | head -20'
Grab 'props.txt'           'getprop'

Write-Host '=== 6) 固件目录清单 ==='
Grab 'fw-vendor.txt'    'ls -lR /vendor/firmware'
Grab 'fw-btfirmware.txt' 'ls -lR /vendor/bt_firmware'
Grab 'fw-libfw.txt'     'ls -lR /vendor/lib/firmware 2>/dev/null'
Grab 'fw-root.txt'      'ls -l /lib/firmware 2>/dev/null'

Write-Host '=== 7) 关键二进制 ==='
GrabFile 'vendor.fdt' '/sys/firmware/fdt'

Write-Host '=== 8) 内核日志（含全部 warning）==='
Grab 'dmesg-full.txt' 'dmesg -n 8'

Write-Host ''
Write-Host "=== 采集完成: $out ==="
Get-ChildItem $out | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,1)}} |
    Sort-Object KB -Descending | Format-Table -AutoSize
"总计 {0} 个文件 / {1:N1} MB" -f (Get-ChildItem $out).Count,
    ((Get-ChildItem $out | Measure-Object Length -Sum).Sum/1MB)
