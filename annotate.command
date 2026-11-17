#!/bin/bash
# Opens the annotation tool for one annotator.
# Mac: double-click this file (it asks which annotator you are), or from a terminal:
#     ./annotate.command 2            ./annotate.command annotator-2
# Linux: bash annotate.command 2.   Windows users: annotate.bat instead.

cd "$(dirname "$0")" || exit 1

# With an argument we were started from a terminal: no "press Enter" pauses.
if [ $# -gt 0 ]; then pause() { :; }; else pause() { read -r -p "Press Enter to close this window." _; }; fi

echo "=== Techno annotator ==="
if [ $# -gt 0 ]; then
  n="${1//[!0-9]/}"            # "annotator-2", "annotator_2" or "2" -> "2"
else
  read -r -p "Which annotator are you? Type 1, 2 or 3 and press Enter: " n
fi
case "$n" in
  1|2|3) ;;
  *) echo "Please type 1, 2 or 3 (for example: ./annotate.command 2)."; pause; exit 1 ;;
esac
sheet="annotator_$n"

# Get the latest sheets (only if this folder is a git checkout).
if [ -d .git ] && command -v git >/dev/null 2>&1; then
  echo "Getting the latest version..."
  if ! git pull --ff-only; then
    echo "Couldn't update automatically (you probably have unsaved local changes)."
    echo "Carrying on with the files you have."
  fi
fi

if [ ! -f "annotations/sheets/$sheet.csv" ]; then
  echo "Can't find annotations/sheets/$sheet.csv"
  pause; exit 1
fi

# Preferred: a small local server (Python standard library) that opens the sheet
# automatically and saves straight into it, in any browser. Runs until Ctrl+C.
py=""
for c in .venv/bin/python python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
    py="$c"; break
  fi
done
if [ -n "$py" ]; then
  "$py" src/02_annotation/04_serve_annotator.py "$sheet"
  pause; exit 0
fi

# Fallback without Python: open the page as a file; the sheet has to be picked by hand.
echo "Python 3 not found, so the sheet can't open automatically."
url="file://${PWD// /%20}/annotations/annotator.html?sheet=$sheet"

# Chrome or Edge can save straight back into the CSV; other browsers download a copy.
opened=""
if [ "$(uname)" = "Darwin" ]; then
  for app in "Google Chrome" "Microsoft Edge"; do
    if [ -d "/Applications/$app.app" ] || [ -d "$HOME/Applications/$app.app" ]; then
      open -a "$app" "$url" && opened="$app" && break
    fi
  done
  [ -z "$opened" ] && open "$url"
else
  for b in google-chrome google-chrome-stable chromium microsoft-edge; do
    if command -v "$b" >/dev/null 2>&1; then
      "$b" "$url" >/dev/null 2>&1 & opened="$b"; break
    fi
  done
  [ -z "$opened" ] && xdg-open "$url"
fi

echo
echo "The tool is open in your browser."
echo "Click 'choose file...' and pick: annotations/sheets/$sheet.csv"
if [ -z "$opened" ]; then
  echo
  echo "NOTE: Chrome or Edge was not found. In this browser 'Save CSV' downloads a copy:"
  echo "move it over annotations/sheets/$sheet.csv after saving."
fi
echo "When you're done: save, then commit and push your sheet."
pause
