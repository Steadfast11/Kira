# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
DIR="${KIRA_DIR:-$HOME/.kira}"
echo "Installing Kira…"
[ -f "$DIR/build.sh" ] || { echo "No Kira source checkout at $DIR. Set KIRA_DIR to your existing source checkout, then run this installer again."; exit 1; }
[ "$(sw_vers -productVersion | cut -d. -f1)" -ge 26 ] || { echo "Kira needs macOS 26 or later."; exit 1; }
if ! xcode-select -p >/dev/null 2>&1; then
  echo "First, Apple's command line tools. A macOS window will open: click Install."
  echo "When it finishes, paste the install line again."
  xcode-select --install 2>/dev/null || true
  exit 1
fi
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull -q --ff-only || { echo "Could not update $DIR. Resolve the Git update error, then try again."; exit 1; }

fi
"$DIR/build.sh" || { echo "Kira could not be built or installed. Fix the error above, then try again."; exit 1; }
open "$HOME/Applications/Kira.app"
echo "Done. The Kira setup window walks you through the rest."
