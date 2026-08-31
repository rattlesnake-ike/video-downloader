#!/bin/bash
# Builds install-video-downloader.sh — a single self-contained file you can
# share. It embeds video_downloader.py and the app icon, so the recipient
# only needs that one file (plus Homebrew).
set -e
cd "$(dirname "$0")"

OUT="install-video-downloader.sh"

cat > "$OUT" << 'HEADER'
#!/bin/bash
# Video Downloader installer for macOS
# Installs dependencies via Homebrew and creates /Applications/Video Downloader.app
# Usage: bash install-video-downloader.sh
set -e

echo "==========================================="
echo " Video Downloader — installer"
echo "==========================================="
echo ""

if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: this installer is for macOS only."
    exit 1
fi

if ! command -v brew &> /dev/null; then
    echo "Homebrew is required but not installed."
    echo "Install it first from https://brew.sh then re-run this script."
    exit 1
fi

# --- Python with tkinter ---------------------------------------------------
have_tk_python() {
    for PY in /opt/homebrew/bin/python3.13 /usr/local/bin/python3.13 \
              /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        if [ -x "$PY" ] && "$PY" -c 'import tkinter' &> /dev/null; then
            return 0
        fi
    done
    return 1
}

echo "Checking for Python with tkinter..."
if have_tk_python; then
    echo "  ✓ found"
else
    echo "  installing python-tk@3.13 via Homebrew..."
    brew install python-tk@3.13
fi

echo "Checking for yt-dlp..."
if command -v yt-dlp &> /dev/null || [ -x /opt/homebrew/bin/yt-dlp ] || [ -x /usr/local/bin/yt-dlp ]; then
    echo "  ✓ found"
else
    echo "  installing yt-dlp via Homebrew..."
    brew install yt-dlp
fi

echo "Checking for ffmpeg (needed to merge video + audio)..."
if command -v ffmpeg &> /dev/null || [ -x /opt/homebrew/bin/ffmpeg ] || [ -x /usr/local/bin/ffmpeg ]; then
    echo "  ✓ found"
else
    echo "  installing ffmpeg via Homebrew (this can take a few minutes)..."
    brew install ffmpeg
fi

# --- App bundle ------------------------------------------------------------
APP_PATH="/Applications/Video Downloader.app"
if [ ! -w "/Applications" ]; then
    APP_PATH="$HOME/Applications/Video Downloader.app"
    mkdir -p "$HOME/Applications"
fi

echo ""
echo "Installing to: $APP_PATH"
rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources"

cat > "$APP_PATH/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key><string>en</string>
    <key>CFBundleExecutable</key><string>Video Downloader</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>CFBundleIdentifier</key><string>com.local.video-downloader</string>
    <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
    <key>CFBundleName</key><string>Video Downloader</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>2.0</string>
    <key>CFBundleVersion</key><string>2</string>
    <key>LSMinimumSystemVersion</key><string>10.13</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
EOF

cat > "$APP_PATH/Contents/MacOS/Video Downloader" << 'EOF'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
for PY in /opt/homebrew/bin/python3.13 /usr/local/bin/python3.13 \
          /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
    if command -v "$PY" &> /dev/null && "$PY" -c 'import tkinter' &> /dev/null; then
        exec "$PY" "$DIR/../Resources/video_downloader.py"
    fi
done
osascript -e 'display alert "Python not found" message "Video Downloader needs Python with tkinter.\n\nInstall it with:\nbrew install python-tk@3.13"'
EOF
chmod +x "$APP_PATH/Contents/MacOS/Video Downloader"

HEADER

# --- embed the Python source ---
cat >> "$OUT" << 'MID1'
cat > "$APP_PATH/Contents/Resources/video_downloader.py" << 'PYEOF'
MID1
cat video_downloader.py >> "$OUT"
cat >> "$OUT" << 'MID2'
PYEOF

MID2

# --- embed the icon as base64 ---
if [ -f AppIcon.icns ]; then
cat >> "$OUT" << 'MID3'
base64 -d > "$APP_PATH/Contents/Resources/AppIcon.icns" << 'ICNEOF'
MID3
base64 -i AppIcon.icns >> "$OUT"
cat >> "$OUT" << 'MID4'
ICNEOF

MID4
fi

cat >> "$OUT" << 'FOOTER'
# ad-hoc codesign so Gatekeeper doesn't complain locally
codesign --force --deep -s - "$APP_PATH" 2>/dev/null || true
# refresh Finder's icon cache for the new app
touch "$APP_PATH"

echo ""
echo "==========================================="
echo " ✓ Done! Video Downloader is installed."
echo "==========================================="
echo ""
echo "Launch it from Applications or Spotlight."
FOOTER

chmod +x "$OUT"
echo "Built $OUT ($(du -h "$OUT" | cut -f1 | tr -d ' '))"
