param(
    [string]$ProjectRoot = "$env:USERPROFILE\Documents\Card Creator Projects\Dark Magic"
)

$ErrorActionPreference = 'Stop'
$dataPath = Join-Path $ProjectRoot 'data\dark-magic-card-data.csv'
$cards = Import-Csv -LiteralPath $dataPath

$canonical = @(
    @('Lockjaw Legionnaire','+1','Lesser Daemon'), @('Grim Cavalier','+1','Lesser Daemon'),
    @('Arcanist Gorger','+1','Lesser Daemon'), @('Chimeric Wall','+0','Lesser Daemon'),
    @('Eldritch Walker','+0','Lesser Daemon'), @('Eclectic Sorcerer','+1','Lesser Daemon'),
    @('Hunted One','+4','Lesser Daemon'), @('Corruption Specter','+2','Lesser Daemon'),
    @('Treasured Offering','+1','Lesser Daemon'), @('Flesh Devourer','+2','Lesser Daemon'),
    @('Blood Cult','+1','Lesser Daemon'), @('Minister of Tithes','+1','Lesser Daemon'),
    @('Recoiling Aberration','+3','Lesser Daemon'), @('Pain Matriarch','+2','Lesser Daemon'),
    @('Traitorous Weaver','+2','Lesser Daemon'), @('Silent Protector','+1','Lesser Daemon'),
    @('Burning Familiar','+2','Lesser Daemon'), @('Devout Hierophant','+1','Lesser Daemon'),
    @('Minister of Spite','+0','Lesser Daemon'), @('Spirit of Famine','+2','Lesser Daemon'),
    @('Fortress Watcher','+0','Lesser Daemon'), @('Scourge of Victors','+2','Lesser Daemon'),
    @('Silent Infiltrator','+1','Lesser Daemon'), @('Treacherous Wolf','+2','Lesser Daemon'),
    @('Solemn Executioner','+3','Lesser Daemon'), @('The Lion-Headed Demiurge','+2','Greater Daemon'),
    @('The Mother of Monstrosity','+3','Greater Daemon'), @('The Inverter of Delights','+1','Greater Daemon'),
    @('The Architect of Plagues','+1','Greater Daemon'), @('The Archangel of War','+2','Greater Daemon'),
    @('The Elder of Extinction','+5','Greater Daemon'), @('The Ancient Covenant','+2','Greater Daemon'),
    @('The Jealous Emperor','+3','Greater Daemon'), @('Raising the Foul','','Invocation Spell'),
    @('Fortean Contract','','Invocation Spell'), @('Divine Intervention','','Invocation Spell'),
    @("Heaven's Pathway",'','Invocation Spell'), @('Goetic Evocation','','Invocation Spell'),
    @('Path of Scourging','','Destruction Spell'), @('Eldritch Assassination','','Destruction Spell'),
    @('Violent Culling','','Destruction Spell'), @('Cruel Snuffing','','Destruction Spell'),
    @('Deadly Visitation','','Destruction Spell'), @('Balancing Act','','Destruction Spell'),
    @('Heroic Entrance','','Destruction Spell'), @('Wrongful Persecution','','Destruction Spell'),
    @('Deadly Alchemy','','Destruction Spell'), @('Hellfire Chalice','','Destruction Spell'),
    @('Coffin Gambit','','Destruction Spell'), @('Unstable Vortex','','Destruction Spell')
)

for ($i = 0; $i -lt $cards.Count; $i++) {
    $cards[$i].title = $canonical[$i][0]
    $cards[$i].cost = $canonical[$i][1]
    $cards[$i].type = $canonical[$i][2]
}

$importPath = Join-Path $ProjectRoot 'data\dark-magic-card-creator-import.csv'
$cards | Select-Object amount,card_number,image,title,cost,type,rules_text | Export-Csv -LiteralPath $importPath -NoTypeInformation -Encoding utf8

$projectId = [guid]::NewGuid().ToString()
$timestamp = (Get-Date).ToUniversalTime()
$unixTimestamp = ([DateTimeOffset]$timestamp).ToUnixTimeSeconds()
$projectInfo = [ordered]@{
    version = 2.12
    project_id = $projectId
    name = 'Dark Magic'
    creation_app_version = '2.14.14'
    creation_date = $timestamp.ToString('o')
    creation_date_unix = $unixTimestamp
    last_modification_app_version = '2.14.14'
    last_modification_date = $timestamp.ToString('o')
    last_modification_date_unix = $unixTimestamp
}
$projectJson = $projectInfo | ConvertTo-Json
$projectJson | Set-Content -LiteralPath (Join-Path $ProjectRoot 'Dark Magic.cc') -Encoding utf8
$projectJson | Set-Content -LiteralPath (Join-Path $ProjectRoot 'data\project.json') -Encoding utf8

$blueprint = Get-Content -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Card Creator\CardCreator_Data\StreamingAssets\Windows\Defaults\DefaultBlueprint.json' -Raw | ConvertFrom-Json
$blueprint.name = 'Dark Magic Faithful Faces'
# Card Creator's project token maps directly to assets/images.  Do not include
# assets/images after the token; nested folders are then resolved correctly.
$cardBackUri = '%PROJECT%/card-back.png'
$blueprint.back_layers[0].panels[0].data.uri = $cardBackUri
$blueprintsDir = Join-Path $ProjectRoot 'data\blueprints'
$cardSetsDir = Join-Path $ProjectRoot 'data\cardsets'
New-Item -ItemType Directory -Force -Path $blueprintsDir,$cardSetsDir | Out-Null
$blueprintPath = Join-Path $blueprintsDir 'dark-magic-blueprint.json'
$blueprint | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $blueprintPath -Encoding utf8

$frontLayerIds = @($blueprint.front_layers | ForEach-Object { $_.layer_id })
$layerOnePanelId = $blueprint.front_layers[0].panels[0].panel_id
$layerTwoPanelId = $blueprint.front_layers[1].panels[0].panel_id
$layerThreeImagePanelId = $blueprint.front_layers[2].panels[0].panel_id
$layerThreeTextPanelId = $blueprint.front_layers[2].panels[1].panel_id
$backLayerId = $blueprint.back_layers[0].layer_id
$backPanelId = $blueprint.back_layers[0].panels[0].panel_id
$cardSetId = [guid]::NewGuid().ToString()
$cardSet = [ordered]@{
    version = 2.12
    cardset_id = $cardSetId
    name = 'Dark Magic'
    blueprint_id = $blueprint.blueprint_id
    hint_order_index = 0
    cards = @(
        foreach ($record in $cards) {
            $faceUri = "%PROJECT%/cards/{0:D2}.png" -f [int]$record.card_number
            $imageData = [ordered]@{
                uri = $faceUri
                mask_uri = ''
                fit_mode = 'fit'
                zoom = 1.0
                offset = '0, 0'
                tint = '#FFFFFFFF'
            }
            [ordered]@{
                card_id = [guid]::NewGuid().ToString()
                amount = [int]$record.amount
                front_layers = @(
                    [ordered]@{
                        blueprint_layer_id = $frontLayerIds[0]
                        panels = @([ordered]@{
                            blueprint_panel_id = $layerOnePanelId
                            enabled = $true
                            rotation = 0
                            padding = '0, 0, 0, 0'
                            type = 'image'
                            data = $imageData
                        })
                    },
                    [ordered]@{
                        blueprint_layer_id = $frontLayerIds[1]
                        panels = @([ordered]@{
                            blueprint_panel_id = $layerTwoPanelId
                            enabled = $false
                            rotation = 0
                            padding = '0, 0, 0, 0'
                            type = 'image'
                            data = [ordered]@{ uri=''; mask_uri=''; fit_mode='fit'; zoom=1.0; offset='0, 0'; tint='#FFFFFFFF' }
                        })
                    },
                    [ordered]@{
                        blueprint_layer_id = $frontLayerIds[2]
                        panels = @(
                            [ordered]@{
                                blueprint_panel_id = $layerThreeImagePanelId
                                enabled = $false
                                rotation = 0
                                padding = '0, 0, 0, 0'
                                type = 'image'
                                data = [ordered]@{ uri=''; mask_uri=''; fit_mode='fit'; zoom=1.0; offset='0, 0'; tint='#FFFFFFFF' }
                            },
                            [ordered]@{
                                blueprint_panel_id = $layerThreeTextPanelId
                                enabled = $false
                                rotation = 0
                                padding = '0, 0, 0, 0'
                                type = 'text'
                                data = [ordered]@{ text=''; color='#333333FF'; outline_length=1.0; outline_color='#FFFFFF00'; image_scaling=1.0; image_offset='0, 0' }
                            }
                        )
                    }
                )
                back_layers = @([ordered]@{
                    blueprint_layer_id = $backLayerId
                    panels = @([ordered]@{
                        blueprint_panel_id = $backPanelId
                        enabled = $true
                        rotation = 0
                        padding = '0, 0, 0, 0'
                        type = 'image'
                        data = [ordered]@{ uri=$cardBackUri; mask_uri=''; fit_mode='fit'; zoom=1.0; offset='0, 0'; tint='#FFFFFFFF' }
                    })
                })
            }
        }
    )
}
$cardSet | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $cardSetsDir 'dark-magic-cardset.json') -Encoding utf8

$readme = @"
# Dark Magic Card Creator conversion

This package preserves all 50 original card faces as individual PNGs under `assets/images/cards/` and the original card back at `assets/images/card-back.png`.

`data/dark-magic-card-creator-import.csv` is the Card Creator import table. It contains the correct title, cost, and card type for every card plus OCR-extracted rules text. Use the card image column as the source image field when creating or editing a Card Creator blueprint. The field text was OCR-extracted and should be proofread before a final print export; the original face image remains the visual source of truth.

The source images retain the original design exactly, including the art, title strip, rules box, card-type strip, and every cost box.
"@
Set-Content -LiteralPath (Join-Path $ProjectRoot 'README.md') -Value $readme -Encoding utf8

"Created $importPath"
