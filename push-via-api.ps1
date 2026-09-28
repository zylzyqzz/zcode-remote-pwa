$ErrorActionPreference = 'Stop'
$token = $env:GH_TOKEN
if (-not $token) { throw 'GH_TOKEN not set' }
$repo = 'zylzyqzz/zcode-remote-pwa'
$dir = 'C:\Users\Administrator\.zcode\workspace\default\zcode-remote-pwa'
$headers = @{
  Authorization = "token $token"
  'User-Agent'  = 'zcode-pwa-deploy'
  Accept        = 'application/vnd.github+json'
}

function Get-FileSha([string]$path) {
  try {
    $one = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repo/contents/$path`?ref=main"
    return $one.sha
  } catch { return $null }
}

# 1) 推送 / 更新文件
$files = @('README.md', 'serve.ps1', 'make-icons-v2.ps1', 'official-icon.png', 'push-via-api.ps1')
foreach ($f in $files) {
  $bytes = [IO.File]::ReadAllBytes((Join-Path $dir ($f -replace '/', '\')))
  $content = [Convert]::ToBase64String($bytes)
  $body = @{
    message = 'chore: complete repo packaging (scripts, source icon) + README structure'
    content = $content
    branch  = 'main'
  }
  $sha = Get-FileSha $f
  if ($sha) { $body.sha = $sha }
  $json = $body | ConvertTo-Json
  try {
    $res = Invoke-RestMethod -Headers $headers -Method Put -Uri "https://api.github.com/repos/$repo/contents/$f" -Body $json -ContentType 'application/json'
    Write-Host "OK  $f  commit=$($res.commit.sha.Substring(0,7))"
  } catch {
    Write-Host "FAIL $f : $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message.Substring(0, [Math]::Min(300, $_.ErrorDetails.Message.Length)) }
  }
}

# 2) 删除遗留的旧版图标（已被官方 Z logo v2 取代）
$delete = @('icon-192.png', 'icon-512.png', 'icon-maskable-512.png')
foreach ($f in $delete) {
  $sha = Get-FileSha $f
  if (-not $sha) { Write-Host "SKIP $f (not in repo)"; continue }
  $body = @{
    message = 'chore: remove legacy green icons (replaced by official Z logo v2)'
    sha     = $sha
    branch  = 'main'
  } | ConvertTo-Json
  try {
    Invoke-RestMethod -Headers $headers -Method Delete -Uri "https://api.github.com/repos/$repo/contents/$f" -Body $body -ContentType 'application/json' | Out-Null
    Write-Host "DEL $f"
  } catch {
    Write-Host "FAIL-DEL $f : $($_.Exception.Message)"
  }
}
