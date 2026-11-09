# Copies skills\comfyui-workflow into ~\.claude\skills and, if ~\.codex exists,
# into ~\.codex\skills. Only that one folder is replaced. Safe to run repeatedly.
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = 'Stop'

$name = 'comfyui-workflow'
$sourceDir = Join-Path (Join-Path $PSScriptRoot 'skills') $name

if (-not (Test-Path -LiteralPath $sourceDir -PathType Container)) {
    Write-Error "$sourceDir not found"
    exit 1
}
if (-not $HOME -or -not (Test-Path -LiteralPath $HOME -PathType Container)) {
    Write-Error 'The home folder could not be found'
    exit 1
}

function Remove-Target([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) {
        # A link or junction: remove the link only, never what it points to.
        if ($item.PSIsContainer) {
            [IO.Directory]::Delete($Path, $false)
        } else {
            [IO.File]::Delete($Path)
        }
    } else {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Install-Skill([string]$SkillsDir) {
    $target = Join-Path $SkillsDir $name
    New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

    if ([IO.Path]::GetFullPath($target).TrimEnd('\', '/') -ieq [IO.Path]::GetFullPath($sourceDir).TrimEnd('\', '/')) {
        Write-Output "unchanged: $target is the source folder itself"
        return
    }

    # Copy first and swap last, so a failed copy leaves the old install intact.
    $staging = Join-Path $SkillsDir (".$name.installing.$PID")
    try {
        if (Test-Path -LiteralPath $staging) {
            Remove-Item -LiteralPath $staging -Recurse -Force
        }
        Copy-Item -LiteralPath $sourceDir -Destination $staging -Recurse -Force
        Get-ChildItem -LiteralPath $staging -Recurse -Force |
            Where-Object { $_.Name -eq '.DS_Store' -or $_.Name -eq '__pycache__' } |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

        # Windows PowerShell's Set-Content -Encoding UTF8 adds a BOM, which would corrupt the path when a shell reads it.
        [IO.File]::WriteAllText((Join-Path $staging 'REPO_PATH'), $PSScriptRoot, (New-Object Text.UTF8Encoding $false))

        if (Test-Path -LiteralPath $target) {
            $action = 'replaced'
            Remove-Target $target
        } else {
            $action = 'installed'
        }
        Move-Item -LiteralPath $staging -Destination $target
    } finally {
        if (Test-Path -LiteralPath $staging) {
            Remove-Item -LiteralPath $staging -Recurse -Force
        }
    }

    $count = @(Get-ChildItem -LiteralPath $target -Recurse -Force -File).Count
    Write-Output "${action}: $target ($count files)"
}

Install-Skill (Join-Path (Join-Path $HOME '.claude') 'skills')

$codexDir = Join-Path $HOME '.codex'
if (Test-Path -LiteralPath $codexDir -PathType Container) {
    Install-Skill (Join-Path $codexDir 'skills')
} else {
    Write-Output "skipped: $codexDir does not exist"
}
