# Reliable SSE test for PowerShell — avoids JSON quoting bugs on -d / --data-raw.
# Usage (from repo root or Backend): .\scripts\test-stream.ps1
# Requires: uvicorn running on http://127.0.0.1:8000

$ErrorActionPreference = "Stop"
$base = if ($env:POCKET_MECHANICS_API_URL) { $env:POCKET_MECHANICS_API_URL.TrimEnd("/") } else { "http://127.0.0.1:8000" }
$bodyPath = Join-Path $PSScriptRoot "stream-body.json"
$json = @'
{"message":"Hi","session_id":"s1"}
'@
[System.IO.File]::WriteAllText($bodyPath, $json.Trim(), [System.Text.UTF8Encoding]::new($false))

Write-Host "POST $base/api/ai/stream (SSE)..." -ForegroundColor Cyan
curl.exe -N -s -S -X POST "$base/api/ai/stream" `
  -H "Content-Type: application/json" `
  --data-binary "@$bodyPath"
