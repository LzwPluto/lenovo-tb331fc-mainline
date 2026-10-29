# alpine.ps1 - run a command inside the Alpine system over the USB serial
# console. Handles the getty login (root / empty password) when needed.
param(
    [string]$Port = $(if($env:ALPINEPORT){$env:ALPINEPORT}else{'COM3'}),
    [string]$Cmd = $(if($env:ALPINE_CMD){$env:ALPINE_CMD}else{''}),
    [int]$Wait = $(if($env:ALPINEWAIT){[int]$env:ALPINEWAIT}else{2500}),
    [switch]$NoAbort
)

$sp = New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$sp.ReadTimeout = 500
$sp.NewLine = "`r`n"
try { $sp.Open() } catch { Write-Output "cannot open $Port : $_"; exit 1 }

function Read-Until($pattern, $timeoutMs) {
    $buf = ''; $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt $timeoutMs) {
        try { $buf += $sp.ReadExisting() } catch {}
        if ($buf -match $pattern) { return $buf }
        Start-Sleep -Milliseconds 120
    }
    return $buf
}

# Send Ctrl-C to abort any running program unless NoAbort is specified
$sp.DiscardInBuffer()
if (-not $NoAbort) {
    $sp.Write([char]3)
    Start-Sleep -Milliseconds 200
}
$sp.Write("`r`n")
$seen = Read-Until '#|login:' 2500

if ($seen -match 'login:') {
    $sp.Write("root`r`n")
    $p = Read-Until 'Password:|#' 4000
    if ($p -match 'Password:') {
        $sp.Write("123456`r`n")
        $seen = Read-Until '#\s*$' 8000
    } else {
        $seen = $p
    }
}

if ($Cmd) {
    $sp.DiscardInBuffer()
    $sp.Write($Cmd + "`r`n")
    $out = Read-Until '#\s*$' (5000 + $Wait)
    # strip the echoed command line
    $lines = $out -split "`r?`n"
    $lines | Where-Object { $_ -ne '' } | ForEach-Object { $_ }
} else {
    Write-Output $seen
}
$sp.Close()
