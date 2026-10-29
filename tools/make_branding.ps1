# Writes every image made from the Neto-IL-TV icon (branding\tv-icon\tv-icon.png, drawn by branding\tv-icon\draw.ps1
# with Fredoka Bold): app icons and TV banner (Android), opening screens on a yellow-gold-orange gradient, the logo in
# the skin's top corner, the add-ons' icons, and the LG icons.
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

function Fill-Gold($g, [int]$w, [int]$h) {
    # Yellow, gold and orange, as on the icon's screen.
    $brush = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 0, $w, $h), ([Drawing.Color]::Gold), ([Drawing.Color]::Orange), 45
    $blend = New-Object Drawing.Drawing2D.ColorBlend 3
    $blend.Colors = @([Drawing.Color]::FromArgb(255, 255, 214, 10), [Drawing.Color]::FromArgb(255, 240, 170, 20), [Drawing.Color]::FromArgb(255, 255, 120, 0))
    $blend.Positions = @([single]0, [single]0.5, [single]1)
    $brush.InterpolationColors = $blend
    $g.FillRectangle($brush, 0, 0, $w, $h)
}

function Save-Png($bmp, [string]$path) { $bmp.Save($path, [Drawing.Imaging.ImageFormat]::Png) }

function Save-Scaled($src, [int]$w, [int]$h, [string]$path) {
    $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
    $g.InterpolationMode = 'HighQualityBicubic'; $g.DrawImage($src, 0, 0, $w, $h); $g.Dispose(); Save-Png $b $path; $b.Dispose()
}

function Save-Screen($logo, [int]$w, [int]$h, [int]$logoSize, [string]$path, [string]$format) {
    # Soft grey screen with the logo in the middle (Android opening screen, Kodi splash): gold is too bright full screen.
    $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
    $g.InterpolationMode = 'HighQualityBicubic'
    $g.FillRectangle((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 0, $w, $h),
        ([Drawing.Color]::FromArgb(255, 84, 86, 92)), ([Drawing.Color]::FromArgb(255, 44, 46, 52)), 90), 0, 0, $w, $h)
    $g.DrawImage($logo, [int](($w - $logoSize) / 2), [int](($h - $logoSize) / 2), $logoSize, $logoSize); $g.Dispose()
    if ($format -eq 'jpg') {
        $enc = [Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/jpeg'
        $ep = New-Object Drawing.Imaging.EncoderParameters 1
        $ep.Param[0] = New-Object Drawing.Imaging.EncoderParameter ([Drawing.Imaging.Encoder]::Quality), ([long]90)
        $b.Save($path, $enc, $ep)
    } else { Save-Png $b $path }
    $b.Dispose()
}

$logo = [Drawing.Image]::FromFile((Join-Path $root 'branding\tv-icon\tv-icon.png'))
New-Item -ItemType Directory -Force (Join-Path $root 'branding') | Out-Null
Save-Png $logo (Join-Path $root 'branding\logo.png')

# App tiles: the TV as large as fits, on the yellow-gold-orange gradient, no text (Android icons and banner, LG icons)
$tv = New-Object Drawing.Rectangle 40, 150, 944, 700   # the TV itself inside the 1024 icon
function Save-Tile([int]$w, [int]$h, [int]$pad, [string]$path) {
    $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
    $g.InterpolationMode = 'HighQualityBicubic'; $g.SmoothingMode = 'AntiAlias'
    Fill-Gold $g $w $h
    $s = [Math]::Min(($w - 2 * $pad) / $tv.Width, ($h - 2 * $pad) / $tv.Height)
    $dw = $tv.Width * $s; $dh = $tv.Height * $s
    $g.DrawImage($logo, (New-Object Drawing.RectangleF (($w - $dw) / 2), (($h - $dh) / 2), $dw, $dh), $tv, 'Pixel')
    $g.Dispose(); Save-Png $b $path; $b.Dispose()
}
Get-ChildItem (Join-Path $work 'res') -Recurse -Filter ic_launcher.png | ForEach-Object {
    $old = [Drawing.Image]::FromFile($_.FullName); $w = $old.Width; $h = $old.Height; $old.Dispose()
    Save-Tile $w $h ([int]($w * 0.05)) $_.FullName
}
Save-Tile 320 180 8 (Join-Path $work 'res\drawable-xhdpi\banner.png')

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
Save-Tile 80 80 4 (Join-Path $root 'webos\assets\icon.png')
Save-Tile 130 130 6 (Join-Path $root 'webos\assets\largeIcon.png')
$logo.Dispose()
Write-Output 'branding written'
