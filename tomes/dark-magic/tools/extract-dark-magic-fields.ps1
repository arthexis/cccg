param(
    [string]$ProjectRoot = "$env:USERPROFILE\Documents\Card Creator Projects\Dark Magic"
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Add-Type -AssemblyName System.Drawing
$tesseract = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
$cardsDir = Join-Path $ProjectRoot 'assets\images\cards'
$fieldDir = Join-Path $ProjectRoot 'temp\fields'
New-Item -ItemType Directory -Force -Path $fieldDir | Out-Null

function Get-OcrText([string]$ImagePath, [string]$OutputBase, [int]$Psm) {
    if (-not (Test-Path "$OutputBase.txt")) {
        & $tesseract $ImagePath $OutputBase --psm $Psm -l eng 2>$null
    }
    if (Test-Path "$OutputBase.txt") {
        $raw = Get-Content "$OutputBase.txt" -Raw
        if ($null -eq $raw) { return '' }
        return ([string]$raw).Trim() -replace "[\r\n]+", ' '
    }
    return ''
}

foreach ($cardPath in Get-ChildItem -LiteralPath $cardsDir -Filter '*.png' | Sort-Object Name) {
    $number = [int]$cardPath.BaseName
    $card = [System.Drawing.Image]::FromFile($cardPath.FullName)
    try {
        $regions = [ordered]@{
            title = [System.Drawing.Rectangle]::new(2, 0, $card.Width - 4, 28)
            rules = [System.Drawing.Rectangle]::new(4, [int]($card.Height * .63), $card.Width - 8, [int]($card.Height * .27))
            type = [System.Drawing.Rectangle]::new(4, [int]($card.Height * .92), $card.Width - 8, [int]($card.Height * .06))
        }
        foreach ($entry in $regions.GetEnumerator()) {
            $fileBase = Join-Path $fieldDir ("{0:D2}-{1}" -f $number, $entry.Key)
            $imagePath = "$fileBase.png"
            if (-not (Test-Path $imagePath)) {
                $crop = [System.Drawing.Bitmap]::new($entry.Value.Width * 4, $entry.Value.Height * 4)
                try {
                    $g = [System.Drawing.Graphics]::FromImage($crop)
                    try {
                        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                        $g.DrawImage($card, [System.Drawing.Rectangle]::new(0, 0, $crop.Width, $crop.Height), $entry.Value, [System.Drawing.GraphicsUnit]::Pixel)
                    }
                    finally { $g.Dispose() }
                    $crop.Save($imagePath, [System.Drawing.Imaging.ImageFormat]::Png)
                }
                finally { $crop.Dispose() }
            }
            $psm = if ($entry.Key -eq 'rules') { 6 } else { 7 }
            Get-OcrText $imagePath $fileBase $psm | Out-Null
        }
    }
    finally { $card.Dispose() }
}

$items = foreach ($cardPath in Get-ChildItem -LiteralPath $cardsDir -Filter '*.png' | Sort-Object Name) {
    $n = [int]$cardPath.BaseName
    $titleOcr = Get-OcrText (Join-Path $fieldDir ("{0:D2}-title.png" -f $n)) (Join-Path $fieldDir ("{0:D2}-title" -f $n)) 7
    $rules = Get-OcrText (Join-Path $fieldDir ("{0:D2}-rules.png" -f $n)) (Join-Path $fieldDir ("{0:D2}-rules" -f $n)) 6
    $type = Get-OcrText (Join-Path $fieldDir ("{0:D2}-type.png" -f $n)) (Join-Path $fieldDir ("{0:D2}-type" -f $n)) 7
    $costMatch = [regex]::Match($titleOcr, '[+\-]\s*\d+')
    $cost = if ($costMatch.Success) { $costMatch.Value -replace '\s', '' } else { '' }
    $title = ($titleOcr -replace '[+\-]\s*\d+','').Trim(' ','|','_','-')
    [pscustomobject]@{
        amount = 1
        card_number = $n
        image = "%PROJECT%/assets/images/cards/$($cardPath.Name)"
        title = $title
        cost = $cost
        type = $type
        rules_text = $rules
    }
}

$items | Export-Csv -LiteralPath (Join-Path $ProjectRoot 'data\dark-magic-card-data.csv') -NoTypeInformation -Encoding utf8
