# 新电脑部署脚本：安装依赖并启动 Qwen 本地问答助手
# 需联网。用法: .\setup.ps1  或  .\setup.ps1 -SkipModel  跳过模型下载

param([switch]$SkipModel)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

function Write-Step { param($msg) Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "    $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "    $msg" -ForegroundColor Yellow }

function Refresh-Path {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath    = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:PATH    = "$machinePath;$userPath"
}

function Download-File {
    param($url, $dest, $label)
    Write-Host "    Downloading $label ..." -ForegroundColor Gray
    $wc = New-Object System.Net.WebClient
    $wc.Proxy = [System.Net.GlobalProxySelection]::GetEmptyWebProxy()
    $wc.DownloadFile($url, $dest)
}

function Clear-Proxy {
    [System.Net.WebRequest]::DefaultWebProxy = [System.Net.GlobalProxySelection]::GetEmptyWebProxy()
    $env:HTTP_PROXY  = ""; $env:HTTPS_PROXY  = ""
    $env:http_proxy  = ""; $env:https_proxy  = ""
    $env:ALL_PROXY   = ""; $env:all_proxy    = ""
    $env:NO_PROXY    = "*"; $env:no_proxy    = "*"
}

# ============================================================
# 1. Check / Install Python 3.12+
# ============================================================
Write-Step "Check Python 3.12+"
$py = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $v = & $cmd -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>$null
        if ($v) {
            $parts = $v -split " "
            if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 12) { $py = $cmd; break }
        }
    } catch {}
}
if (-not $py) {
    Write-Warn "Python not found. Auto-installing Python 3.12..."
    $pyInstaller = Join-Path $env:TEMP "python-3.12.10-amd64.exe"
    $pyUrls = @(
        "https://mirrors.huaweicloud.com/python/3.12.10/python-3.12.10-amd64.exe",
        "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
    )
    $downloaded = $false
    foreach ($url in $pyUrls) {
        try { Download-File $url $pyInstaller "Python 3.12"; $downloaded = $true; break }
        catch { Write-Host "    Source failed, trying next..." -ForegroundColor Gray }
    }
    if (-not $downloaded) {
        Write-Host "    ERROR: Could not download Python installer." -ForegroundColor Red
        exit 1
    }
    Write-Host "    Installing Python 3.12 (silent)..." -ForegroundColor Gray
    $installArgs = "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0"
    Start-Process -FilePath $pyInstaller -ArgumentList $installArgs -Wait -NoNewWindow
    Remove-Item $pyInstaller -Force -ErrorAction SilentlyContinue
    Refresh-Path
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $v = & $cmd -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>$null
            if ($v) {
                $parts = $v -split " "
                if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 12) { $py = $cmd; break }
            }
        } catch {}
    }
    if (-not $py) {
        Write-Host "    ERROR: Python install failed." -ForegroundColor Red
        exit 1
    }
    Write-Ok "Python installed: $py"
} else {
    Write-Ok "Python: $py"
}

# ============================================================
# 2. Install uv
# ============================================================
Write-Step "Check uv"
$uv = $null
try { $uv = Get-Command uv -ErrorAction SilentlyContinue } catch {}
if (-not $uv) {
    Write-Warn "Installing uv..."
    Clear-Proxy
    $mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"
    Write-Host "    Installing uv via pip (Tsinghua mirror)..." -ForegroundColor Gray
    & $py -m pip install uv -q -i $mirror --trusted-host pypi.tuna.tsinghua.edu.cn
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    Mirror failed, trying default PyPI..." -ForegroundColor Gray
        & $py -m pip install uv -q
    }
    if ($LASTEXITCODE -eq 0) {
        Refresh-Path
        Write-Ok "uv installed"
    } else {
        Write-Host "    ERROR: Could not install uv." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Ok "uv exists"
}


# ============================================================
# 2.5 Install Visual C++ Redistributable (torch 依赖)
# ============================================================
Write-Step "Check Visual C++ Redistributable"
$vcKey = "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64"
$vcKey2 = "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
$hasVC = (Test-Path $vcKey) -or (Test-Path $vcKey2)
if (-not $hasVC) {
    Write-Warn "Visual C++ Redistributable not found. Installing..."
    $vcInstaller = Join-Path $env:TEMP "vc_redist.x64.exe"
    $vcUrls = @(
        "https://aka.ms/vs/17/release/vc_redist.x64.exe",
        "https://download.microsoft.com/download/vc_redist.x64.exe"
    )
    $downloaded = $false
    foreach ($url in $vcUrls) {
        try { Download-File $url $vcInstaller "Visual C++ Redistributable"; $downloaded = $true; break }
        catch { Write-Host "    Source failed, trying next..." -ForegroundColor Gray }
    }
    if (-not $downloaded) {
        Write-Host "    ERROR: Could not download VC++ Redistributable." -ForegroundColor Red
        exit 1
    }
    Write-Host "    Installing Visual C++ Redistributable (silent)..." -ForegroundColor Gray
    Start-Process -FilePath $vcInstaller -ArgumentList "/quiet /norestart" -Wait -NoNewWindow
    Remove-Item $vcInstaller -Force -ErrorAction SilentlyContinue
    Write-Ok "Visual C++ Redistributable installed"
} else {
    Write-Ok "Visual C++ Redistributable exists"
}

# ============================================================
# 3. Check / Install Node.js
# ============================================================
Write-Step "Check Node.js"
$node = $null
try { $node = Get-Command node -ErrorAction SilentlyContinue } catch {}
if (-not $node) {
    Write-Warn "Node.js not found. Auto-installing Node.js LTS..."
    $nodeInstaller = Join-Path $env:TEMP "node-lts-x64.msi"
    $nodeUrls = @(
        "https://mirrors.huaweicloud.com/nodejs/v22.15.0/node-v22.15.0-x64.msi",
        "https://nodejs.org/dist/v22.15.0/node-v22.15.0-x64.msi"
    )
    $downloaded = $false
    foreach ($url in $nodeUrls) {
        try { Download-File $url $nodeInstaller "Node.js LTS"; $downloaded = $true; break }
        catch { Write-Host "    Source failed, trying next..." -ForegroundColor Gray }
    }
    if (-not $downloaded) {
        Write-Host "    ERROR: Could not download Node.js installer." -ForegroundColor Red
        exit 1
    }
    Write-Host "    Installing Node.js (silent)..." -ForegroundColor Gray
    $msiArgs = "/i `"$nodeInstaller`" /quiet /norestart ADDLOCAL=ALL"
    Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -NoNewWindow
    Remove-Item $nodeInstaller -Force -ErrorAction SilentlyContinue
    Refresh-Path
    try { $node = Get-Command node -ErrorAction SilentlyContinue } catch {}
    if (-not $node) {
        Write-Host "    ERROR: Node.js install failed." -ForegroundColor Red
        exit 1
    }
    Write-Ok "Node.js installed: $(node -v)"
} else {
    Write-Ok "Node: $(node -v)"
}

# ============================================================
# 4. Install Python deps (uv sync)
# ============================================================
Write-Step "Install Python deps (uv sync)"
Clear-Proxy
$env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
Write-Host "    Using Tsinghua mirror for PyPI" -ForegroundColor Gray
Push-Location $root
try {
    # --no-install-package torch：跳过 torch 安装，由 Step 4.5 单独装 GPU 版
    # 避免 uv 因找不到 torch 而报依赖解析失败
    uv sync --no-install-package torch
    Write-Ok "Python deps done"
} finally {
    Pop-Location
}

# ============================================================
# 4.5 Install PyTorch (GPU / CUDA)
# ============================================================
Write-Step "Install PyTorch (GPU)"
$uvPy = Join-Path $root ".venv\Scripts\python.exe"

# 检测 CUDA 是否可用
$cudaOk = $false
try {
    $cudaOk = [bool](& $uvPy -c "import torch; print(torch.cuda.is_available())" 2>$null | Select-String "True")
} catch {}

if (-not $cudaOk) {
    # 读取驱动支持的最高 CUDA 版本
    $cudaVer = $null
    try {
        $smiOut = & nvidia-smi 2>$null
        if ($smiOut) {
            $match = [regex]::Match(($smiOut -join " "), "CUDA Version:\s*([\d]+)\.([\d]+)")
            if ($match.Success) {
                $cudaMajor = [int]$match.Groups[1].Value
                $cudaMinor = [int]$match.Groups[2].Value
                # PyTorch 目前最高支持 cu124，按驱动版本选择
                if     ($cudaMajor -ge 12 -and $cudaMinor -ge 4) { $cudaVer = "cu124" }
                elseif ($cudaMajor -ge 12)                        { $cudaVer = "cu121" }
                elseif ($cudaMajor -ge 11 -and $cudaMinor -ge 8) { $cudaVer = "cu118" }
            }
        }
    } catch {}

    if ($cudaVer) {
        Write-Host "    Detected driver CUDA $cudaMajor.$cudaMinor → installing torch ($cudaVer)..." -ForegroundColor Gray
        $torchIndex = "https://download.pytorch.org/whl/$cudaVer"
        uv pip install torch --index-url $torchIndex --reinstall
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "PyTorch ($cudaVer) installed"
        } else {
            Write-Warn "PyTorch GPU install failed, falling back to CPU (Tsinghua)..."
            uv pip install torch -i "https://pypi.tuna.tsinghua.edu.cn/simple" --reinstall
            if ($LASTEXITCODE -eq 0) { Write-Ok "PyTorch (CPU) installed" }
        }
    } else {
        Write-Warn "nvidia-smi not found, installing CPU torch (Tsinghua)..."
        uv pip install torch -i "https://pypi.tuna.tsinghua.edu.cn/simple" --reinstall
        if ($LASTEXITCODE -eq 0) { Write-Ok "PyTorch (CPU) installed" }
        else { Write-Warn "If you have an NVIDIA GPU, run: uv pip install torch --index-url https://download.pytorch.org/whl/cu124 --reinstall" }
    }
} else {
    Write-Ok "PyTorch CUDA already available, skipping"
}

# ============================================================
# 5. Install frontend deps (npm install)
# ============================================================
Write-Step "Install frontend deps (npm install)"
Push-Location (Join-Path $root "frontend")
try {
    npm install --registry=https://registry.npmmirror.com
    Write-Ok "Frontend deps done"
} finally {
    Pop-Location
}

# ============================================================
# 6. Model download (optional)
# ============================================================
$modelDir = Join-Path $root "qwen\Qwen3___5-4B"
$hasWeights = $false
if (Test-Path $modelDir) {
    $hasWeights = [bool](Get-ChildItem $modelDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(safetensors|bin)$" })
}
if (-not $SkipModel -and -not $hasWeights) {
    Write-Step "Download model (Qwen3.5-4B, ~8-10GB)"
    Push-Location $root
    try {
        uv run python (Join-Path $root "src/download_model.py")
    } finally {
        Pop-Location
    }
} elseif ($SkipModel) {
    Write-Warn "Model download skipped. Place model in: $modelDir"
} else {
    Write-Ok "Model exists"
}

# ============================================================
# 6.5 Pre-download RAG models (bge-small-zh, bge-reranker)
# ============================================================
Write-Step "Pre-download RAG models (domestic mirror)"
$env:HF_ENDPOINT = "https://hf-mirror.com"
Push-Location $root
try {
    & (Join-Path $root ".venv\Scripts\python.exe") (Join-Path $root "src/download_rag_models.py")
    if ($LASTEXITCODE -eq 0) { Write-Ok "RAG models cached" }
    else { Write-Warn "RAG pre-download failed, will download on first use" }
} catch {
    Write-Warn "RAG pre-download skipped: $_"
} finally {
    Pop-Location
}

# ============================================================
# 7. Create desktop shortcut
# ============================================================
Write-Step "Create desktop shortcut"
$desktop      = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Qwen.lnk"
$iconPath     = Join-Path $root "icon.ico"
$WshShell     = New-Object -ComObject WScript.Shell
$shortcut     = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath       = Join-Path $root "run.bat"
$shortcut.WorkingDirectory = $root
if (Test-Path $iconPath) { $shortcut.IconLocation = (Resolve-Path $iconPath).Path + ",0" }
$shortcut.Description = "Qwen"
$shortcut.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WshShell) | Out-Null
Write-Ok "Desktop shortcut: Qwen.lnk"

# ============================================================
# 8. Launch app
# ============================================================
Write-Step "Launch app"
Write-Host ""
Write-Host "  Ready. Starting..." -ForegroundColor Green
Write-Host "  Close browser tab or Ctrl+C to exit" -ForegroundColor Gray
Write-Host ""
Start-Sleep -Seconds 1
$env:HF_ENDPOINT = "https://hf-mirror.com"
Push-Location $root
try {
    & (Join-Path $root ".venv\Scripts\python.exe") start.py
} finally {
    Pop-Location
}