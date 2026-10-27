# resetwatch.ps1 -- 判定 TB331FC 从 B 槽启动失败时到底发生了什么。
#
# 注意：`fastboot reboot` 之后 fastboot 界面消失是【必然的】，不是信号。
# 真正的信号是下面三个量：
#   T_back : 从重启到 fastboot 重新出现的时间
#   flaps  : 重新出现的次数（>1 说明在连续复位 = boot loop）
#   retry  : slot-retry-count:b 有没有变化
#
# 解读:
#   flaps == 0                -> 一直没回 fastboot：要么真的启动了，要么卡黑屏
#   flaps == 1, T_back 短      -> ABL 走完一轮就退回 fastboot（中止或内核早 panic）
#   flaps == 1, T_back 长      -> 多了一整轮复位的开销，倾向"内核 panic 后复位"
#   flaps >= 2                -> 明确的反复复位（内核阶段在崩）
#
# 只读 + 只重启，不写入任何分区，绝不碰 A 槽。

param(
    [string]$Fastboot = 'D:\搞机助手\fastboot.exe',
    [int]$PollMs = 150,
    [int]$TotalSeconds = 60
)

$ErrorActionPreference = 'Continue'

function FB { param([string[]]$a) & $Fastboot @a 2>&1 }
function FbPresent {
    $out = & $Fastboot devices 2>&1
    return [bool]($out | Where-Object { $_ -match '\S+\s+fastboot' })
}

Write-Host '================ 0. 重启前状态 ================' -ForegroundColor Cyan
$slot = (FB @('getvar', 'current-slot') | Out-String)
if ($slot -match 'current-slot:\s*a') {
    Write-Host '!! 当前是 A 槽 —— 本脚本拒绝在 A 槽上运行。' -ForegroundColor Red
    exit 1
}
Write-Host ($slot.Trim())
Write-Host ((FB @('getvar','slot-retry-count:b') | Where-Object { $_ -match 'retry' }) -join "`n")
Write-Host ((FB @('getvar','slot-unbootable:b') | Where-Object { $_ -match 'unbootable' }) -join "`n")
$preRetry = [int]((FB @('getvar','slot-retry-count:b') | Out-String) -replace '[^\d]','' | ForEach-Object { if ($_ -eq '') { -1 } else { $_ } })
Write-Host "A 槽: " -NoNewline
Write-Host (((FB @('getvar','slot-successful:a')) | Where-Object { $_ -match 'successful' }) -join "`n") -ForegroundColor Green

Write-Host ''
Write-Host '================ 1. 重启并采样 ================' -ForegroundColor Cyan
$t0 = Get-Date
$events = @()
$last = $true
$events += [pscustomobject]@{ ms = 0; present = $true }

& $Fastboot reboot 2>&1 | Out-Null

while (((Get-Date) - $t0).TotalSeconds -lt $TotalSeconds) {
    $p = FbPresent
    if ($p -ne $last) {
        $ms = [int](((Get-Date) - $t0).TotalMilliseconds)
        $events += [pscustomobject]@{ ms = $ms; present = $p }
        $label = if ($p) { '出现' } else { '消失' }
        $color = if ($p) { 'Yellow' } else { 'DarkGray' }
        Write-Host ('  {0,6} ms   fastboot {1}' -f $ms, $label) -ForegroundColor $color
        $last = $p
    }
    Start-Sleep -Milliseconds $PollMs
}

Write-Host ''
Write-Host '================ 2. 时间线摘要 ================' -ForegroundColor Cyan
$events | Format-Table -AutoSize | Out-String | Write-Host

$gone = $events | Where-Object { -not $_.present }
$backs = @()
for ($i = 1; $i -lt $events.Count; $i++) {
    if ($events[$i].present -and -not $events[$i - 1].present) { $backs += $events[$i].ms }
}
$tGone = if ($gone) { $gone[0].ms } else { -1 }
$flaps = $backs.Count

Write-Host ''
Write-Host '================ 3. 判定 ================' -ForegroundColor Cyan
Write-Host ("fastboot 首次消失 : {0} ms" -f $tGone)
Write-Host ("重新出现次数 flaps : {0}   时刻: {1}" -f $flaps, ($(if ($backs) { ($backs -join ', ') + ' ms' } else { '-' })))

if ($flaps -eq 0) {
    Write-Host ''
    Write-Host '=> 设备在 60 s 内【没有】回到 fastboot。' -ForegroundColor Green
    Write-Host '   可能性 1：这套镜像其实启动成功了（只是屏幕不亮 / 面板没驱动）。' -ForegroundColor Green
    Write-Host '   可能性 2：卡在黑屏错误页或挂死。' -ForegroundColor Green
    Write-Host '   区分办法：看屏幕有没有任何变化；或长按电源 10 s 后是否回到 fastboot。' -ForegroundColor Green
}
elseif ($flaps -eq 1) {
    Write-Host ''
    Write-Host ("=> 设备重启后 {0} ms 回到 fastboot，只回来了一次。" -f $backs[0]) -ForegroundColor Yellow
    if ($backs[0] -lt 6000) {
        Write-Host '   倾向：单轮启动尝试后 ABL 退回 fastboot（中止，或内核极早 panic）。' -ForegroundColor Yellow
    } else {
        Write-Host '   倾向：比"纯 ABL 中止"多花了一轮时间，内核阶段 panic 后复位的可能性上升。' -ForegroundColor Yellow
    }
}
else {
    Write-Host ''
    Write-Host ("=> 反复复位 {0} 次（boot loop）。" -f $flaps) -ForegroundColor Magenta
    Write-Host '   这基本可以确定：ABL 交接是成功的，是内核/rootfs 阶段在崩。' -ForegroundColor Magenta
}

Write-Host ''
Write-Host '================ 4. 重启后变量 ================' -ForegroundColor Cyan
$postRetryLine = ((FB @('getvar','slot-retry-count:b')) | Where-Object { $_ -match 'retry' }) -join "`n"
Write-Host $postRetryLine
Write-Host (((FB @('getvar','slot-unbootable:b')) | Where-Object { $_ -match 'unbootable' }) -join "`n")
Write-Host (((FB @('getvar','slot-successful:a'))  | Where-Object { $_ -match 'successful' }) -join "`n") -ForegroundColor Green
Write-Host ''
if ($postRetryLine -match ':\s*(\d+)') {
    $postRetry = [int]$Matches[1]
    if ($preRetry -ge 0) {
        Write-Host ("retry-count:b : {0} -> {1}" -f $preRetry, $postRetry) -ForegroundColor Yellow
        if ($postRetry -eq $preRetry) {
            Write-Host '  没变。注意 ABL 里有 "A/B retry count NOT decremented" 这条分支，没变不能反推执行位置。' -ForegroundColor DarkGray
        } elseif ($postRetry -lt $preRetry) {
            Write-Host '  减了 -> ABL 认为这次算一次真实启动尝试（走到了跳转内核那一步）。' -ForegroundColor Yellow
        }
    }
}
Write-Host ''
Write-Host '回滚（如果需要）： fastboot --set-active=a ; fastboot reboot' -ForegroundColor Cyan
