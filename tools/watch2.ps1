# watch2.ps1 -- 可靠的启动结果判定。
#
# resetwatch.ps1 的判据有盲点：ABL 失败后【回落 A 槽进 Android】时 fastboot 也不会返回，
# 会被误判成 flaps=0（"可能启动成功"）。本脚本同时轮询 fastboot 和 adb，并读回槽位，
# 把四种结局区分开：
#   1) fastboot 重新出现        -> ABL 中止
#   2) adb 出现且槽位 = _a      -> ABL 回落 A 槽（B 失败）
#   3) adb 出现且槽位 = _b      -> 真的从 B 槽启动了（里程碑！）
#   4) 两者都没有               -> 挂死，或从 B 槽启动了但没有 adb
param(
    [string]$Fastboot = 'D:\搞机助手\fastboot.exe',
    [string]$Adb = 'D:\搞机助手\adb.exe',
    [int]$Seconds = 70,
    [int]$PollMs = 500
)

$t0 = Get-Date
$fbAt = $null; $adbAt = $null
& $Fastboot reboot 2>&1 | Out-Null

while (((Get-Date) - $t0).TotalSeconds -lt $Seconds) {
    $ms = [int](((Get-Date) - $t0).TotalMilliseconds)
    if (-not $fbAt) {
        $o = & $Fastboot devices 2>&1
        if ($o | Where-Object { $_ -match '\S+\s+fastboot' }) {
            $fbAt = $ms
            Write-Host ("  {0,6} ms  fastboot 出现" -f $ms) -ForegroundColor Yellow
        }
    }
    if (-not $adbAt) {
        $o = & $Adb devices 2>&1
        if ($o | Where-Object { $_ -match '\S+\s+device$' }) {
            $adbAt = $ms
            Write-Host ("  {0,6} ms  adb 出现" -f $ms) -ForegroundColor Cyan
        }
    }
    if ($fbAt -and $adbAt) { break }
    Start-Sleep -Milliseconds $PollMs
}

Write-Host ''
Write-Host '================ 判定 ================' -ForegroundColor Cyan
Write-Host ("fastboot 出现: {0}" -f $(if ($fbAt) { "$fbAt ms" } else { '否' }))
Write-Host ("adb      出现: {0}" -f $(if ($adbAt) { "$adbAt ms" } else { '否' }))

if ($adbAt) {
    $slot = (& $Adb shell "getprop ro.boot.slot_suffix" 2>&1) -join ''
    $fp = (& $Adb shell "getprop ro.build.fingerprint" 2>&1) -join ''
    Write-Host ("槽位: {0}" -f $slot.Trim())
    Write-Host ("指纹: {0}" -f $fp.Trim())
    if ($slot -match '_a') {
        Write-Host '=> ABL 回落 A 槽进 Android。B 槽启动失败（但设备可用）。' -ForegroundColor Magenta
    } elseif ($slot -match '_b') {
        Write-Host '=> ★ 从 B 槽启动了！' -ForegroundColor Green
    }
} elseif ($fbAt) {
    Write-Host '=> ABL 中止并回到 fastboot。' -ForegroundColor Magenta
} else {
    Write-Host '=> 70 s 内既无 fastboot 也无 adb：挂死，或从 B 槽启动但无 adb。' -ForegroundColor Green
}

Write-Host ''
Write-Host '================ B 槽属性 ================' -ForegroundColor Cyan
if ($fbAt) {
    & $Fastboot getvar slot-retry-count:b 2>&1 | Where-Object { $_ -match 'retry-count:b' }
    & $Fastboot getvar slot-unbootable:b 2>&1 | Where-Object { $_ -match 'unbootable' }
    & $Fastboot getvar current-slot 2>&1 | Where-Object { $_ -match 'current-slot' }
} else {
    Write-Host '(不在 fastboot，需 adb reboot bootloader 后再读)'
}
