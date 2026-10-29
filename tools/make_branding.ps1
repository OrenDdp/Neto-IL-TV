# Draws the Neto-IL-TV logo and writes every image made from it: app icons and TV banner (Android), opening screen,
# the logo in the skin's top corner, the add-ons' icons, and the LG icons.
#     powershell -NoProfile -ExecutionPolicy Bypass -File tools\make_branding.ps1
Add-Type -AssemblyName System.Drawing
$root = Split-Path -Parent $PSScriptRoot
$work = Join-Path $root 'work'

function New-Logo([int]$size) {
    # Rounded square in Israeli blue, "NETO" over "IL TV".
    $b = New-Object Drawing.Bitmap $size, $size
    $g = [Drawing.Graphics]::FromImage($b)
    $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'; $g.Clear([Drawing.Color]::Transparent)
    $r = [int]($size * 0.18)
    $path = New-Object Drawing.Drawing2D.GraphicsPath
    $path.AddArc(0, 0, 2 * $r, 2 * $r, 180, 90); $path.AddArc($size - 2 * $r - 1, 0, 2 * $r, 2 * $r, 270, 90)
    $path.AddArc($size - 2 * $r - 1, $size - 2 * $r - 1, 2 * $r, 2 * $r, 0, 90); $path.AddArc(0, $size - 2 * $r - 1, 2 * $r, 2 * $r, 90, 90)
    $path.CloseFigure()
    $rect = New-Object Drawing.Rectangle 0, 0, $size, $size
    $fill = New-Object Drawing.Drawing2D.LinearGradientBrush $rect, ([Drawing.Color]::FromArgb(255, 0, 56, 184)), ([Drawing.Color]::FromArgb(255, 8, 24, 72)), 90
    $g.FillPath($fill, $path)
    $fmt = New-Object Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
    $big = New-Object Drawing.Font('Segoe UI Black', [single]($size * 0.26), [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Pixel)
    $small = New-Object Drawing.Font('Segoe UI Semibold', [single]($size * 0.14), [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Pixel)
    $g.DrawString('NETO', $big, [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 0, ([single]($size * 0.12)), $size, ([single]($size * 0.45))), $fmt)
    $light = New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(255, 150, 200, 255))
    $g.DrawString('IL TV', $small, $light, (New-Object Drawing.RectangleF 0, ([single]($size * 0.55)), $size, ([single]($size * 0.3))), $fmt)
    $g.Dispose(); return $b
}

function Save-Png($bmp, [string]$path) { $bmp.Save($path, [Drawing.Imaging.ImageFormat]::Png) }

function Save-Scaled($src, [int]$w, [int]$h, [string]$path) {
    $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
    $g.InterpolationMode = 'HighQualityBicubic'; $g.DrawImage($src, 0, 0, $w, $h); $g.Dispose(); Save-Png $b $path; $b.Dispose()
}

function Save-Screen($logo, [int]$w, [int]$h, [int]$logoSize, [string]$path, [string]$format) {
    # Black screen with the logo in the middle (Android opening screen, Kodi splash).
    $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
    $g.InterpolationMode = 'HighQualityBicubic'; $g.Clear([Drawing.Color]::Black)
    $g.DrawImage($logo, [int](($w - $logoSize) / 2), [int](($h - $logoSize) / 2), $logoSize, $logoSize); $g.Dispose()
    if ($format -eq 'jpg') {
        $enc = [Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/jpeg'
        $ep = New-Object Drawing.Imaging.EncoderParameters 1
        $ep.Param[0] = New-Object Drawing.Imaging.EncoderParameter ([Drawing.Imaging.Encoder]::Quality), ([long]90)
        $b.Save($path, $enc, $ep)
    } else { Save-Png $b $path }
    $b.Dispose()
}

$logo = New-Logo 1024
New-Item -ItemType Directory -Force (Join-Path $root 'branding') | Out-Null
Save-Png $logo (Join-Path $root 'branding\logo.png')

# Android app icons (sizes as shipped) and the TV banner
Get-ChildItem (Join-Path $work 'res') -Recurse -Filter ic_launcher.png | ForEach-Object {
    $old = [Drawing.Image]::FromFile($_.FullName); $w = $old.Width; $h = $old.Height; $old.Dispose()
    Save-Scaled $logo $w $h $_.FullName
}
$banner = New-Object Drawing.Bitmap 320, 180; $g = [Drawing.Graphics]::FromImage($banner)
$g.SmoothingMode = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'; $g.TextRenderingHint = 'AntiAliasGridFit'
$g.Clear([Drawing.Color]::FromArgb(255, 8, 24, 72)); $g.DrawImage($logo, 20, 20, 140, 140)
$fmt = New-Object Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
$g.DrawString('Neto-IL-TV', (New-Object Drawing.Font('Segoe UI', 26, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Pixel)),
    [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 165, 0, 150, 180), $fmt)
$g.Dispose(); Save-Png $banner (Join-Path $work 'res\drawable-xhdpi\banner.png'); $banner.Dispose()

# Opening screens
foreach ($p in 'res\drawable\applaunch_screen.png', 'res\drawable-xxxhdpi\applaunch_screen.png', 'assets\media\applaunch_screen.png') {
    Save-Screen $logo 1920 1080 560 (Join-Path $work $p) 'png'
}
Save-Screen $logo 1920 1080 560 (Join-Path $work 'assets\media\splash.jpg') 'jpg'

# Skin corner logo and add-on icons
$addons = Join-Path $work 'assets\addons'
Save-Scaled $logo 256 256 (Join-Path $addons 'skin.fentastic\media\logos\netotv.png')
Save-Scaled $logo 256 256 (Join-Path $addons 'service.netotv\icon.png')
Save-Scaled $logo 256 256 (Join-Path $addons 'plugin.video.netotv\icon.png')

# LG icons
Save-Scaled $logo 80 80 (Join-Path $root 'webos\assets\icon.png')
Save-Scaled $logo 130 130 (Join-Path $root 'webos\assets\largeIcon.png')
$logo.Dispose()
Write-Output 'branding written'
