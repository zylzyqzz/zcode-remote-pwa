$ErrorActionPreference = 'Stop'
$root = "C:\Users\Administrator\.zcode\workspace\default\zcode-remote-pwa"
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:8123/")
$listener.Start()
Write-Host "serving $root at http://127.0.0.1:8123/"
$mime = @{
  ".html" = "text/html; charset=utf-8"; ".js" = "text/javascript; charset=utf-8"
  ".json" = "application/json"; ".webmanifest" = "application/manifest+json"
  ".png" = "image/png"; ".ico" = "image/x-icon"
}
while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  try {
    $path = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath)
    if ($path -eq "/") { $path = "/index.html" }
    $file = Join-Path $root $path.TrimStart("/").Replace("/", "\")
    if ((Test-Path $file -PathType Leaf) -and ($file.StartsWith($root))) {
      $ext = [IO.Path]::GetExtension($file).ToLower()
      $type = if ($mime.ContainsKey($ext)) { $mime[$ext] } else { "application/octet-stream" }
      $bytes = [IO.File]::ReadAllBytes($file)
      $ctx.Response.ContentType = $type
      $ctx.Response.Headers.Add("Service-Worker-Allowed", "/")
      $ctx.Response.ContentLength64 = $bytes.Length
      $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
      $ctx.Response.StatusCode = 404
    }
  } catch { $ctx.Response.StatusCode = 500 }
  finally { $ctx.Response.OutputStream.Close() }
}
