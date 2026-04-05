#!/bin/bash
# =============================================================================
# Bing Wallpaper - Download Today's Wallpaper
# Universal: Linux / macOS / Windows (Git Bash, WSL, Cygwin)
# =============================================================================

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/config.conf" ]; then
    source "$SCRIPT_DIR/config.conf"
else
    echo "⚠️  config.conf not found, using defaults"
    WALLPAPER_DIR="${WALLPAPER_DIR:-docs/img}"
    BING_MARKET="${BING_MARKET:-it-IT}"
    SAVE_METADATA="${SAVE_METADATA:-true}"
    GENERATE_GALLERY="${GENERATE_GALLERY:-true}"
    FILENAME_FORMAT='bing-{date}.jpg'
    ARCHIVE_LANG="${ARCHIVE_LANG:-IT-it}"
fi

# Create folder if it doesn't exist
mkdir -p "$WALLPAPER_DIR"

# Bing API URL
API_URL="https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=$BING_MARKET"

echo "🖼️  Bing Wallpaper - Daily Download"
echo "📁 Destination: $WALLPAPER_DIR"
echo "🌐 Market: $BING_MARKET"
echo ""

# Download JSON
JSON=$(curl -s "$API_URL" 2>/dev/null)

if [ -z "$JSON" ]; then
    echo "❌ Error: unable to connect to Bing"
    exit 1
fi

# Extract fields
if command -v jq &>/dev/null; then
    IMG_PATH=$(echo "$JSON" | jq -r '.images[0].url')
    STARTDATE=$(echo "$JSON" | jq -r '.images[0].enddate')
    HASH=$(echo "$JSON" | jq -r '.images[0].hsh')
    FULLSTARTDATE=$(echo "$JSON" | jq -r '.images[0].fullstartdate')
    # Extract copyright string and parse title/copyright
    COPYRIGHT_FULL=$(echo "$JSON" | jq -r '.images[0].copyright')
    # Extract copyright (text between parentheses) and title (rest)
    REGEX='^(.*)\(([^)]+)\)$'
    if [[ "$COPYRIGHT_FULL" =~ $REGEX ]]; then
        TITLE="${BASH_REMATCH[1]}"
        TITLE="${TITLE% }"  # Remove trailing space
        COPYRIGHT="${BASH_REMATCH[2]}"
    else
        TITLE="$COPYRIGHT_FULL"
        COPYRIGHT=""
    fi
else
    echo "❌ Error: unable to extract fields (jq not found)"
    exit 1
fi

# Verify extracted data
if [ -z "$IMG_PATH" ]; then
    echo "❌ Error: unable to extract image URL"
    exit 1
fi

# Build filename
HASH_SHORT="${HASH:0:8}"
FILENAME="$FILENAME_FORMAT"
FILENAME="${FILENAME/\{date\}/$STARTDATE}"
FILENAME="${FILENAME/\{hash\}/$HASH_SHORT}"
TITLE_CLEAN=$(echo "$TITLE" | tr -cd '[:alnum:]_-')
FILENAME="${FILENAME/\{title\}/$TITLE_CLEAN}"
DEST="$WALLPAPER_DIR/$FILENAME"

# Full image URL (high resolution)
FULL_URL="https://www.bing.com$IMG_PATH"

# Download only if it doesn't already exist
if [ -f "$DEST" ]; then
    echo "✅ Already present: $STARTDATE - $TITLE"
    echo "   File: $DEST"
    exit 0
fi

echo "📥 Download: $STARTDATE"
echo "   Title: $TITLE"
echo "   Copyright: $COPYRIGHT"
echo "   File: $FILENAME"
echo "   URL: $FULL_URL"
echo "   api: $API_URL"
echo ""

# Download image
curl -sL "$FULL_URL" -o "$DEST"

if [ $? -ne 0 ] || [ ! -s "$DEST" ]; then
    echo "❌ Download error"
    rm -f "$DEST" 2>/dev/null
    exit 1
fi

# Add watermark with metadata (if ImageMagick is available)
if command -v convert &>/dev/null && [ -n "$TITLE" ] && [ -n "$COPYRIGHT" ]; then
    echo "🎨 Adding watermark..."
    # Get image width for responsive text sizing
    IMG_WIDTH=$(identify -format "%w" "$DEST" 2>/dev/null || echo "1920")
    # Font size proportional to image width (~2% of width)
    FONT_SIZE=$((IMG_WIDTH / 50))
    [ "$FONT_SIZE" -lt 12 ] && FONT_SIZE=12

    # Title in top-left, Copyright in bottom-right with shadow for readability
    convert "$DEST" \
        -gravity NorthWest \
        -fill "rgba(255,255,255,0.9)" \
        -stroke "rgba(0,0,0,0.5)" \
        -strokewidth 1 \
        -pointsize "$FONT_SIZE" \
        -annotate +$((FONT_SIZE))+$((FONT_SIZE)) "$TITLE" \
        -gravity SouthEast \
        -annotate +$((FONT_SIZE))+$((FONT_SIZE)) "$COPYRIGHT" \
        "$DEST.tmp" && mv "$DEST.tmp" "$DEST"
    echo "✅ Watermark added"
fi

# Save metadata (optional)
if [ "$SAVE_METADATA" = "true" ]; then
    cat > "${DEST%.*}.txt" << EOF
Title: $TITLE
Copyright: $COPYRIGHT
Date: $STARTDATE
Full Date: $FULLSTARTDATE
Hash: $HASH
URL: $FULL_URL
Market: $BING_MARKET
Source: Bing Daily Wallpaper
EOF
    echo "📝 Metadata saved"
fi

echo ""
echo "✅ Download complete: $DEST"

exit 0
