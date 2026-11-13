# Dark Magic Card Creator conversion

This package preserves all 50 original card faces as individual PNGs under ssets/images/cards/ and the original card back at ssets/images/card-back.png.

data/dark-magic-card-creator-import.csv is the Card Creator import table. It contains the correct title, cost, and card type for every card plus OCR-extracted rules text. Use the card image column as the source image field when creating or editing a Card Creator blueprint. The field text was OCR-extracted and should be proofread before a final print export; the original face image remains the visual source of truth.

The source images retain the original design exactly, including the art, title strip, rules box, card-type strip, and every cost box.
