# Package for customer - excludes .venv, node_modules, .next, .git, qwen
# Output: qwen-local-YYYYMMDD.zip

param([string]$OutDir = "")

$root = Split-Path $PSScriptRoot -Parent   # 项目根目录
if ([string]::IsNullOrEmpty($OutDir)) { $OutDir = $root }
$zipName = "qwen-local-" + [DateTime]::Now.ToString("yyyyMMdd") + ".zip"
$zip = [System.IO.Path]::Combine($OutDir, $zipName)
$temp = Join-Path $env:TEMP "qwen-pack-$(Get-Random)"

Write-Host ">>> Packaging to: $zip" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $temp -Force | Out-Null

try {
    robocopy $root $temp /E /XD .venv node_modules .next .git __pycache__ qwen rag_db /XF *.pyc .env pack.ps1 /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed" }
    Compress-Archive -Path "$temp\*" -DestinationPath $zip -Force
    $size = [math]::Round((Get-Item $zip).Length / 1MB, 2)
    Write-Host ">>> Done: $zip ($size MB)" -ForegroundColor Green
} finally {
    Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
}
