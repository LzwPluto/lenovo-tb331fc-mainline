# test_ath_debug.ps1 - 打开 ath10k 调试并抓取卡点日志
#
# 前提：已刷入带 CONFIG_ATH10K_DEBUG 的内核，且 ADSP 已 running。

$ErrorActionPreference = 'Continue'
$alpine = 'D:\TB331FCLinux\tools\alpine.ps1'

function RunAlpine([string]$cmd, [string]$wait = '30000') {
    $env:ALPINE_CMD = $cmd
    $env:ALPINEWAIT = $wait
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $alpine 2>&1
}

Write-Host '=== 1) 确认 ADSP / QRTR 就绪 ==='
RunAlpine @'
echo "adsp = $(cat /sys/class/remoteproc/remoteproc1/state 2>/dev/null)"
readlink /sys/bus/rpmsg/devices/a400000.remoteproc:glink-edge.IPCRTR.-1.-1/driver 2>/dev/null || echo "IPCRTR not bound"
'@ '12000'

Write-Host '=== 2) 打开 ath10k 全部调试位 ==='
RunAlpine @'
ls /sys/module/ath10k_core/parameters/ 2>/dev/null
echo 0xffffffff > /sys/module/ath10k_core/parameters/debug_mask 2>&1 && echo "debug_mask set: $(cat /sys/module/ath10k_core/parameters/debug_mask)"
'@ '12000'

Write-Host '=== 3) 重载 ath10k 并抓日志 ==='
RunAlpine @'
dmesg -C
rmmod ath10k_snoc 2>/dev/null; sleep 2
modprobe ath10k_snoc 2>&1; echo "rc=$?"
sleep 20
echo "=== dmesg ==="
dmesg | grep -iE "ath10k|qmi|wlan|wlfw" | tail -60
echo "=== wiphy ==="
ls /sys/class/ieee80211/ 2>/dev/null || echo none
'@ '60000'
