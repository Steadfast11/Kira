#!/bin/bash
# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
# Installs Kira: builds Kira.app, starts it at login, and (re)starts it now. Run it again after any change.
# KIRA_RELEASE_ZIP=/path/Kira.zip ./build.sh only packages a downloadable app: no install, no source path, ad hoc signed.
set -e; cd "$(dirname "$0")"
VERSION=$(tr -d '\n' < VERSION)
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Invalid VERSION: $VERSION"; exit 1; }
IFS=. read -r VERSION_MAJOR VERSION_MINOR VERSION_PATCH <<< "$VERSION"
(( VERSION_MINOR < 1000 && VERSION_PATCH < 1000 )) || { echo "VERSION components must be below 1000"; exit 1; }
BUILD=$((VERSION_MAJOR * 1000000 + VERSION_MINOR * 1000 + VERSION_PATCH))
[ "$(sw_vers -productVersion | cut -d. -f1)" -ge 26 ] || { echo "Kira needs macOS 26 or later (it uses Apple's new on-device speech)."; exit 1; }
xcode-select -p >/dev/null 2>&1 || { echo "Needs Apple's command line tools. Run: xcode-select --install   then run ./build.sh again."; exit 1; }
command -v python3 >/dev/null || { echo "Kira needs Python 3. Install it, then run ./build.sh again."; exit 1; }
command -v claude >/dev/null || [ -x ~/.local/bin/claude ] || echo "Note: Claude Code is not installed yet. Kira's setup window can install it, or you can pick Devin or Pi."
mkdir -p "$HOME/Applications"
STAGE=$(mktemp -d "$HOME/Applications/.kira-install.XXXXXX")
TARGET="$HOME/Applications/Kira.app"
cleanup() {
  if [ -d "$STAGE/previous.app" ] && [ ! -e "$TARGET" ]; then
    mv "$STAGE/previous.app" "$TARGET" || { echo "Could not restore Kira; previous app remains at $STAGE/previous.app"; return; }
  fi
  rm -rf "$STAGE"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
# A compiler error must leave the installed app and its resources alone.
swiftc -O -target "$(uname -m)-apple-macos26.0" Kira.swift -o "$STAGE/Kira"
APP="$STAGE/Kira.app"   # assemble and sign everything before replacing the installed app
# A fresh bundle also removes pages deleted from ui/; failed copies leave the installed app intact.
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/ui/boot"
cp kira.py kokoro_say.py speech_runtime.py access_policy.py "$APP/Contents/Resources/"
cp ui/*.html ui/*.js "$APP/Contents/Resources/ui/"
cp ui/boot/*.m4a ui/boot/timings.json "$APP/Contents/Resources/ui/boot/"   # the boot's recorded voice and sounds (tools/make_boot_voice.py)
cp ui/AppIcon.icns "$APP/Contents/Resources/"
SOURCE_DIR=$(pwd)   # updates pull from this checkout; a downloadable app has none and updates from GitHub Releases
if [ -n "$KIRA_RELEASE_ZIP" ]; then SOURCE_DIR=""; fi
cat > "$APP/Contents/Info.plist" <<P
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>com.kira.app</string>
<key>NSHumanReadableCopyright</key><string>Copyright © 2026 Xasan Abdukhafizov</string>
<key>CFBundleName</key><string>Kira</string>
<key>CFBundleExecutable</key><string>Kira</string>
<key>CFBundleVersion</key><string>$BUILD</string>
<key>CFBundleShortVersionString</key><string>$VERSION</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleIconFile</key><string>AppIcon</string>
<key>KiraSource</key><string>$SOURCE_DIR</string>
<key>LSUIElement</key><true/>
<key>NSMicrophoneUsageDescription</key><string>Kira listens when you use its shortcut or microphone button.</string>
<key>NSAppleEventsUsageDescription</key><string>Kira controls apps like Finder, Chrome and Music when you ask it to.</string>
<key>NSCalendarsFullAccessUsageDescription</key><string>Kira reads your calendar, adds events you request, and asks before moving or deleting existing events. Calendar details are sent to your chosen AI model.</string>
<key>NSSpeechRecognitionUsageDescription</key><string>Kira turns your words into text on this Mac.</string>
</dict></plist>
P
mv "$STAGE/Kira" "$APP/Contents/MacOS/Kira"
# With a code-signing identity named "Kira Local Signing" in the keychain, macOS keeps permissions across
# rebuilds and auto-updates; ad hoc signing would ask for every permission again after each one. So make it once.
ID=$(security find-identity -p codesigning | awk '/Kira Local Signing/{print $2; exit}')
if [ -z "$ID" ]; then
  K=$(mktemp -d)
  /usr/bin/openssl req -x509 -newkey rsa:2048 -nodes -days 7300 -subj "/CN=Kira Local Signing" -addext "extendedKeyUsage=critical,codeSigning" \
    -addext "keyUsage=critical,digitalSignature" -keyout "$K/k.pem" -out "$K/c.pem" 2>/dev/null &&
  /usr/bin/openssl pkcs12 -export -inkey "$K/k.pem" -in "$K/c.pem" -out "$K/a.p12" -passout pass:kira 2>/dev/null &&
  security import "$K/a.p12" -P kira -T /usr/bin/codesign >/dev/null 2>&1 || true   # fails quietly: ad hoc still works
  rm -rf "$K"
  ID=$(security find-identity -p codesigning | awk '/Kira Local Signing/{print $2; exit}')
fi
if [ -n "$KIRA_RELEASE_ZIP" ]; then ID=""; fi   # a downloadable app is signed ad hoc, not with this Mac's identity
codesign -s "${ID:--}" --force "$APP"
codesign --verify --strict "$APP"
if [ -n "$KIRA_RELEASE_ZIP" ]; then
  ditto -c -k --sequence --keepParent "$APP" "$KIRA_RELEASE_ZIP"
  echo "Packaged $KIRA_RELEASE_ZIP"
  exit 0
fi
# Same-filesystem renames: the exit trap restores the previous app if promotion fails.
if [ -e "$TARGET" ]; then mv "$TARGET" "$STAGE/previous.app"; fi
mv "$APP" "$TARGET"
APP="$TARGET"
# register with macOS, or System Settings can't list it for permissions
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP"
AGENT=~/Library/LaunchAgents/com.kira.app.plist   # starts at login, restarts if it crashes (Quit stays quit)
mkdir -p ~/Library/LaunchAgents ~/.config/kira
cat > "$AGENT" <<P
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.kira.app</string>
<key>ProgramArguments</key><array><string>$APP/Contents/MacOS/Kira</string></array>
<key>RunAtLoad</key><true/>
<key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
<key>StandardErrorPath</key><string>$HOME/.config/kira/app.err</string>
</dict></plist>
P
[ -n "$KIRA_NO_RESTART" ] && exit 0   # the app's own updater restarts it when idle
# Reload the job so launchd refreshes its executable signing requirement after a rebuild.
launchctl bootout gui/$(id -u)/com.kira.app 2>/dev/null || true
pkill -f "$APP/Contents/MacOS/Kira$" 2>/dev/null && sleep 1   # stop a copy opened by hand too
# bootout can return before the job has finished unloading.
launchctl bootstrap gui/$(id -u) "$AGENT" 2>/dev/null || { sleep 1; launchctl bootstrap gui/$(id -u) "$AGENT" 2>/dev/null || {
  echo "Could not add Kira to Login Items; opening it directly instead."
  open "$APP"
}; }
echo "Kira is running. Hold Control+Option+Space and talk."
