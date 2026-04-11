#!/bin/bash
# =============================================================================
# Bing Wallpaper - Sync Historical Archive (npanuhin/Bing-Wallpaper-Archive)
# Universal: Linux / macOS / Windows
# =============================================================================

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/config.conf" ]; then
    source "$SCRIPT_DIR/config.conf"
else
    WALLPAPER_DIR="${WALLPAPER_DIR:-docs/img}"
    ARCHIVE_BASE="${ARCHIVE_BASE:-https://raw.githubusercontent.com/npanuhin/Bing-Wallpaper-Archive/refs/heads/master/api}"
    ARCHIVE_LANG="${ARCHIVE_LANG:-US/en}"
    BATCH_SIZE="${BATCH_SIZE:-30}"
    DOWNLOAD_DELAY="${DOWNLOAD_DELAY:-3}"
    SAVE_METADATA="${SAVE_METADATA:-true}"
fi

# Check for jq dependency
if ! command -v jq &>/dev/null; then
    echo "❌ Error: jq is required for this script"
    echo "   Install jq first:"
    echo "   - Debian/Ubuntu: sudo apt install jq"
    echo "   - macOS: brew install jq"
    echo "   - Windows: choco install jq"
    exit 1
fi

mkdir -p "$WALLPAPER_DIR"

echo "🔄 Sync with Bing Wallpaper Archive (npanuhin)"
echo "📍 Region: $ARCHIVE_LANG"
echo "📁 Folder: $WALLPAPER_DIR"
echo "📦 Batch size: $BATCH_SIZE images"
echo ""

# Download complete metadata
METADATA_FILE="$SCRIPT_DIR/.archive-cache.json"
echo "📥 Downloading metadata from archive..."

curl -s "$ARCHIVE_BASE/$ARCHIVE_LANG.json" -o "$METADATA_FILE"

if [ ! -s "$METADATA_FILE" ]; then
    echo "❌ Error: unable to download metadata from $ARCHIVE_BASE"
    echo "   Check your internet connection or that the archive is accessible"
    exit 1
fi

# Count available images
if command -v jq &>/dev/null; then
    TOTAL_AVAILABLE=$(jq 'length' "$METADATA_FILE")
else
    TOTAL_AVAILABLE=$(grep -c '"date"' "$METADATA_FILE" || echo "0")
fi

echo "✅ Found $TOTAL_AVAILABLE images in archive"
echo ""

# Count already downloaded images
ALREADY_DOWNLOADED=$(find "$WALLPAPER_DIR" -name "bing-*.txt" -type f 2>/dev/null | wc -l)
echo "📁 Images already present: $ALREADY_DOWNLOADED"
echo ""

# Download missing images
echo "📥 Checking for missing images..."
echo ""

DOWNLOADED=0
SKIPPED=0
ERRORS=0

# Process all images (from newest to oldest)
process_image() {
    local IMAGE="$1"

    if command -v jq &>/dev/null; then
        DATE=$(echo "$IMAGE" | jq -r '.date // empty')
        TITLE=$(echo "$IMAGE" | jq -r '.title // .caption // .subtitle // "No title available"')
        COPYRIGHT=$(echo "$IMAGE" | jq -r '.copyright // "© No copyright info available"')
        IMG_URL=$(echo "$IMAGE" | jq -r '.url // empty')
    else
        echo "❌ Error: unable to extract fields (jq not found)"
        exit 1
    fi

    [ -z "$DATE" ] && return 1
    [ -z "$IMG_URL" ] && return 1

    # Date format: 2024-01-16 → 20240116
    DATE_FILE=$(echo "$DATE" | tr -d '-')
    HASH=$(echo "$IMG_URL" | grep -oP '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 | tr -d '-')
    [ -z "$HASH" ] && HASH="$DATE_FILE"
    TITLE_CLEAN=$(echo "$TITLE" | tr -cd '[:alnum:]_-')
    FILENAME="bing-${DATE_FILE}.jpg"
    DEST="$WALLPAPER_DIR/$FILENAME"

    if [ -f "${DEST%.*}.txt" ]; then
        echo "   ⏭️  Skip: $DATE - $TITLE"
        return 2  # Return 2 for skipped (already exists)
    fi

    # Delay to respect the server
    sleep "$DOWNLOAD_DELAY"

    # Download image
    echo "   📥 Download: $DATE - $TITLE"
    curl -sL "$IMG_URL" -o "$DEST"

    if [ $? -eq 0 ] && [ -s "$DEST" ]; then
        # Add watermark with metadata (if ImageMagick is available)
        if command -v convert &>/dev/null && [ -n "$TITLE" ] && [ -n "$COPYRIGHT" ]; then
            echo "🎨 Adding watermark..."
            # Get image width for responsive text sizing
            IMG_WIDTH=$(identify -format "%w" "$DEST" 2>/dev/null || echo "3840")
            # Font size proportional to image width (~1% of width)
            FONT_SIZE=$((IMG_WIDTH / 100))
            [ "$FONT_SIZE" -lt 6 ] && FONT_SIZE=6

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

        # Save metadata
        if [ "$SAVE_METADATA" = "true" ]; then
            cat > "${DEST%.*}.txt" << EOF
Title: $TITLE
Copyright: $COPYRIGHT
Date: $DATE_FILE
Original Date: $DATE
Source: npanuhin/Bing-Wallpaper-Archive
Original URL: $IMG_URL
EOF
        fi
        return 0
    else
        echo "   ❌ Error: $DATE"
        rm -f "$DEST" 2>/dev/null
        return 1
    fi
}

# Read and process images (sorted by date descending - newest first)
while IFS= read -r IMAGE; do
    process_image "$IMAGE"
    result=$?
    
    if [ $result -eq 0 ]; then
        DOWNLOADED=$((DOWNLOADED + 1))
    elif [ $result -eq 2 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        ERRORS=$((ERRORS + 1))
    fi

    # Check batch limit (only count actual downloads)
    if [ $DOWNLOADED -ge $BATCH_SIZE ]; then
        echo ""
        echo "⚠️  Batch limit reached ($BATCH_SIZE images)"
        break
    fi

done < <(jq -c 'sort_by(.date | gsub("-"; "") | tonumber) | reverse | .[]' "$METADATA_FILE")

# Final statistics
TOTAL_NOW=$(find "$WALLPAPER_DIR" -name "bing-*.jpg" -type f 2>/dev/null | wc -l)

echo ""
echo "═══════════════════════════════════════════════════"
echo "📊 Summary:"
echo "   Total images in folder: $TOTAL_NOW"
echo "   Downloads performed today: $DOWNLOADED"
echo "   Skipped (already present): $SKIPPED"
echo "   Errors: $ERRORS"
echo "═══════════════════════════════════════════════════"
echo ""

if [ $DOWNLOADED -ge $BATCH_SIZE ]; then
    echo "💡 To download more images, run again:"
    echo "   $SCRIPT_DIR/sync-archive.sh"
    echo ""
    echo "   Or increase BATCH_SIZE in config.conf"
fi

exit 0
