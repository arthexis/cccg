param(
    [string]$OutputRoot = "$env:USERPROFILE\Documents\Card Creator Projects\Dark Magic"
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$sourceSheet = "$env:USERPROFILE\Documents\My Games\Tabletop Simulator\Mods\Images\httpssteamusercontentaakamaihdnetugc16792418993243989945C11A2D50C1A71340C770FB2C516286AC37727DF.png"
$sourceBack = "$env:USERPROFILE\Documents\My Games\Tabletop Simulator\Mods\Images\httpssteamusercontentaakamaihdnetugc1679241899324400456E8AE2EC481D8F64C4A78F4B5DB6FC0FF4A6BAC40.png"
$facesDir = Join-Path $OutputRoot 'assets\images\cards'
$ocrDir = Join-Path $OutputRoot 'temp\ocr'
$dataDir = Join-Path $OutputRoot 'data'

New-Item -ItemType Directory -Path $facesDir,$ocrDir,$dataDir -Force | Out-Null

$sheet = [System.Drawing.Image]::FromFile($sourceSheet)
try {
    $columns = 10
    $rows = 5
    $cardWidth = [int]($sheet.Width / 10)
    $cardHeight = [int]($sheet.Height / 7)
    for ($row = 0; $row -lt $rows; $row++) {
        for ($column = 0; $column -lt $columns; $column++) {
            $index = ($row * $columns) + $column + 1
            $rect = [System.Drawing.Rectangle]::new($column * $cardWidth, $row * $cardHeight, $cardWidth, $cardHeight)
            $card = [System.Drawing.Bitmap]::new($cardWidth, $cardHeight)
            try {
                $graphics = [System.Drawing.Graphics]::FromImage($card)
                try { $graphics.DrawImage($sheet, [System.Drawing.Rectangle]::new(0, 0, $cardWidth, $cardHeight), $rect, [System.Drawing.GraphicsUnit]::Pixel) }
                finally { $graphics.Dispose() }
                $card.Save((Join-Path $facesDir ('{0:D2}.png' -f $index)), [System.Drawing.Imaging.ImageFormat]::Png)
            }
            finally { $card.Dispose() }
        }
    }
}
finally { $sheet.Dispose() }

Copy-Item -LiteralPath $sourceBack -Destination (Join-Path $OutputRoot 'assets\images\card-back.png') -Force

$tesseract = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
$rows = foreach ($cardFile in Get-ChildItem -LiteralPath $facesDir -Filter '*.png' | Sort-Object Name) {
    $base = Join-Path $ocrDir $cardFile.BaseName
    if (-not (Test-Path "$base.txt")) {
        & $tesseract $cardFile.FullName $base --psm 6 -l eng 2>$null
    }
    $ocr = if (Test-Path "$base.txt") { [string]::Concat((Get-Content -LiteralPath "$base.txt" -Raw)).Trim() } else { '' }
    [pscustomobject]@{
        amount = 1
        card_number = [int]$cardFile.BaseName
        image = "%PROJECT%/assets/images/cards/$($cardFile.Name)"
        title = ''
        cost = ''
        type = ''
        rules_text = ''
        ocr_raw = $ocr -replace "[\r\n]+", ' '
    }
}

$rows | Export-Csv -LiteralPath (Join-Path $OutputRoot 'data\dark-magic-ocr.csv') -NoTypeInformation -Encoding utf8
