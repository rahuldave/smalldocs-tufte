#!/bin/sh
# Build the theme's four files in _extensions/tufte/ from src/ and Bootstrap 5.3.8 in vendor/bootstrap/.
#   tufte.css, tufte-dark.css: all of Bootstrap, then the ET Book fonts, the colours of the mode, and the Tufte rules (for smalldocs)
#   tufte.scss, tufte-dark.scss: the same rules as Quarto's Sass layers, with the fonts embedded (for Quarto)
# Run it from anywhere: sh scripts/build.sh
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BS=$ROOT/vendor/bootstrap/bootstrap.min.css
SRC=$ROOT/src
OUT=$ROOT/_extensions/tufte
bs() { sed 's|/\*# sourceMappingURL=[^*]*\*/||' "$BS"; echo; }
{ bs; cat "$SRC/fonts.css" "$SRC/light-root.css" "$SRC/light-dark-parts.css" "$SRC/common.css"; } > "$OUT/tufte.css"
# the dark file also has Bootstrap's dark colour mode on the whole page, as Bootswatch's dark themes do
{ bs; python3 "$ROOT/scripts/dark_root.py" "$BS"; cat "$SRC/fonts.css" "$SRC/dark.css" "$SRC/common.css"; } > "$OUT/tufte-dark.css"
# Quarto looks for a url() from the project, not from the extension, so its fonts are embedded as data URIs
{ cat "$SRC/defaults-light.scss"; echo; echo '/*-- scss:rules --*/'; python3 "$ROOT/scripts/embed_fonts.py" "$SRC/fonts.css" "$OUT"; cat "$SRC/light-root.css" "$SRC/common.css" "$SRC/quarto.css"; } > "$OUT/tufte.scss"
# tufte-dark.scss comes after tufte.scss in Quarto's dark theme, so it holds only the dark colours
{ cat "$SRC/defaults-dark.scss"; echo; echo '/*-- scss:rules --*/'; cat "$SRC/dark.css"; } > "$OUT/tufte-dark.scss"
