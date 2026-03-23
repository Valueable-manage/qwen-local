# Create desktop shortcut, double-click to start frontend+backend
# Icon: icon.ico in project root | Target: run.bat

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Qwen.lnk"
$iconPath = Join-Path $root "icon.ico"

# 先删除旧快捷方式，避免图标缓存残留
if (Test-Path $shortcutPath) { Remove-Item $shortcutPath -Force }

# 清除 Windows 图标缓存
$iconCacheDb = "$env:LOCALAPPDATA\IconCache.db"
if (Test-Path $iconCacheDb) {
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Remove-Item $iconCacheDb -Force -ErrorAction SilentlyContinue
}

$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $root "run.bat"
$shortcut.WorkingDirectory = $root
if (Test-Path $iconPath) {
    $shortcut.IconLocation = (Resolve-Path $iconPath).Path + ",0"
}
$shortcut.Description = "Qwen"
$shortcut.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WshShell) | Out-Null

# 重启 explorer 并刷新桌面图标
Start-Process explorer
Start-Sleep -Milliseconds 800
# 通知 Windows 刷新图标
$shell = New-Object -ComObject Shell.Application
$shell.Windows() | ForEach-Object { $_.Refresh() }
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null

Write-Host ">>> Created: Qwen.lnk" -ForegroundColor Green
Write-Host "    Double-click to start" -ForegroundColor Gray