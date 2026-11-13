# Dark Magic tome

An archival and editable record of the Dark Magic Tabletop Simulator game.

## Contents

- `rules.txt` — rules transcribed from the current Tabletop Simulator save.
- `rules-analysis.md` — identified contradictions, missing definitions, and
  implementation mismatches.
- `tabletop-simulator/` — the current save, Workshop source, and the original
  card-sheet and card-back images.
- `card-creator/` — a 50-card Card Creator project, including individual card
  faces, card back, native project metadata, and structured card/OCR CSV data.
- `tools/` — PowerShell scripts used to extract the faces, OCR fields, and
  generate the Card Creator project.

## Card Creator project

Open `card-creator/Dark Magic.cc` in Steam Card Creator. Image references use
Card Creator's native `%PROJECT%/…` form, which maps to
`card-creator/assets/images/`. The original 50 faces are retained as complete
PNG images, so their art, titles, rules text, and cost boxes are preserved.

`dark-magic-card-creator-import.csv` is the editable import table. Its OCR
rules text should be proofread against the face images before a print export;
the original card face remains the source of truth.

## Provenance

The archive was extracted locally from Workshop item `2868927524` and the
latest local Tabletop Simulator save (`TS_Save_37.json`). It is provided for
preservation and further game-development work.
