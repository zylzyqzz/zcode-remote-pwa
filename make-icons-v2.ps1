Add-Type -AssemblyName System.Drawing
$dir = "C:\Users\Administrator\.zcode\workspace\default\zcode-remote-pwa"
$src = [System.Drawing.Image]::FromFile("$dir\official-icon.png")

function Save-Resized([System.Drawing.Image]$img, [int]$size, [string]$file) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.DrawImage($img, 0, 0, $size, $size)
    $bmp.Save("$dir\$file", [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Host "saved $file"
}

Save-Resized $src 192 "icon-192.png"
Save-Resized $src 512 "icon-512.png"

# maskable：纯色底 + logo 缩到安全区（72%）
$bmp = New-Object System.Drawing.Bitmap(512, 512)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g.Clear([System.Drawing.Color]::FromArgb(255, 14, 15, 17))
$s = [int](512 * 0.72)
$off = [int]((512 - $s) / 2)
$g.DrawImage($src, $off, $off, $s, $s)
$bmp.Save("$dir\icon-maskable-512.png", [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "saved icon-maskable-512.png"
$src.Dispose()
