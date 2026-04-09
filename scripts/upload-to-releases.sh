#!/bin/bash
# =============================================================================
# Bing Wallpaper - Upload Images to GitHub Releases
# Uses GitHub CLI (gh) - no token needed, authenticates via git credentials
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/config.conf" ]; then
    source "$SCRIPT_DIR/config.conf"
fi

WALLPAPER_DIR="${WALLPAPER_DIR:-docs/img}"
RELEASE_TAG="wallpapers-archive"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Upload Images to GitHub Releases${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# Check gh CLI is installed
if ! command -v gh &>/dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) not found${NC}"
    echo "   Install: sudo apt install gh  (Debian/Ubuntu)"
    echo "            brew install gh      (macOS)"
    exit 1
fi

# Authenticate for CI (GitHub Actions)
if [ -n "$GITHUB_TOKEN" ]; then
    echo "   Using GITHUB_TOKEN for CI authentication..."
    echo "$GITHUB_TOKEN" | gh auth login --with-token
fi

# Check authenticated
if ! gh auth status &>/dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub${NC}"
    echo "   Run: gh auth login"
    echo "   Or set GITHUB_TOKEN environment variable"
    exit 1
fi

echo -e "${GREEN}✅ Authenticated as: $(gh api user --jq '.login')${NC}"

# Check images exist
JPG_COUNT=$(find "$WALLPAPER_DIR" -maxdepth 1 \( -name "bing-*.jpg" -o -name "bing_*.jpg" \) -type f 2>/dev/null | wc -l)
THUMB_COUNT=$(find "$WALLPAPER_DIR/thumbs" \( -name "bing-*.jpg" -o -name "bing_*.jpg" \) -type f 2>/dev/null | wc -l)

if [ "$JPG_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No images found${NC}"
    exit 1
fi

echo -e "${GREEN}📸 Images to upload: $JPG_COUNT (thumbnails stay local)${NC}"
echo ""

# Get or create release
echo -e "${YELLOW}📦 Preparing release: $RELEASE_TAG${NC}"

RELEASE_URL=$(gh release view "$RELEASE_TAG" --json url --jq '.url' 2>/dev/null || echo "")

if [ -z "$RELEASE_URL" ]; then
    echo "   Creating new release..."
    gh release create "$RELEASE_TAG" \
        --title "Bing Wallpapers Archive" \
        --notes "Daily Bing wallpapers - auto updated" \
        --latest=false 2>/dev/null
    echo -e "${GREEN}   ✅ Release created${NC}"
else
    echo -e "${GREEN}   ✅ Release exists: $RELEASE_URL${NC}"
fi

# Get existing assets from local cache (if available)
UPLOADED_CACHE="$SCRIPT_DIR/.release-uploaded.json"
declare -A ASSET_MAP

if [ -f "$UPLOADED_CACHE" ]; then
    echo "   Loading from local cache..."
    while IFS= read -r name; do
        [ -n "$name" ] && ASSET_MAP["$name"]=1
    done < <(jq -r '.[]' "$UPLOADED_CACHE" 2>/dev/null)
    echo -e "${GREEN}   Cache: ${#ASSET_MAP[@]} files${NC}"
else
    echo "   Loading from remote release..."
    EXISTING_ASSETS=$(gh release view "$RELEASE_TAG" --json assets --jq '.assets[].name' 2>/dev/null || echo "")
    while IFS= read -r asset; do
        [ -n "$asset" ] && ASSET_MAP["$asset"]=1
    done <<< "$EXISTING_ASSETS"
    echo -e "${GREEN}   Remote: ${#ASSET_MAP[@]} files${NC}"
fi

# Save/update local cache
printf '%s\n' "${!ASSET_MAP[@]}" | jq -R -s 'split("\n") | map(select(length > 0))' > "$UPLOADED_CACHE"
echo ""

# Upload function
upload_asset() {
    local file="$1"
    local name="$2"

    if [[ -n "${ASSET_MAP[$name]}" ]]; then
        echo -e "  ⏭️  $name (exists)"
        return 2
    fi

    if gh release upload "$RELEASE_TAG" "$file" --clobber 2>/dev/null; then
        ASSET_MAP["$name"]=1
        echo -e "  ✅ $name"
        return 0
    else
        echo -e "  ❌ $name"
        return 1
    fi
}

# Upload images
UPLOADED=0
SKIPPED=0
ERRORS=0

echo -e "${YELLOW}📤 Uploading images...${NC}"
while IFS= read -r img; do
    [ -f "$img" ] || continue
    filename=$(basename "$img")

    upload_asset "$img" "$filename"
    result=$?

    if [ $result -eq 0 ]; then
        UPLOADED=$((UPLOADED + 1))
    elif [ $result -eq 2 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        ERRORS=$((ERRORS + 1))
    fi

    sleep 0.5
done < <(find "$WALLPAPER_DIR" -maxdepth 1 \( -name "bing-*.jpg" -o -name "bing_*.jpg" \) -type f 2>/dev/null | sort -r)

echo ""
echo "═══════════════════════════════════════════"
echo -e "${GREEN}📊 Summary:${NC}"
echo -e "   Uploaded: $UPLOADED"
echo -e "   Skipped: $SKIPPED"
echo -e "   Errors: $ERRORS"
echo ""
echo -e "${BLUE}🔗 $RELEASE_URL${NC}"
echo "═══════════════════════════════════════════"

# Generate manifest
echo ""
echo -e "${YELLOW}📝 Generating manifest...${NC}"

ASSETS=$(gh release view "$RELEASE_TAG" --json assets --jq '.assets[].name' 2>/dev/null)

cat > "$WALLPAPER_DIR/releases-manifest.json" << 'EOF'
{
  "release_tag": "wallpapers-archive",
  "base_url": "https://github.com/wafy80/wafy80.github.io/releases/download/wallpapers-archive",
  "images": {
EOF

FIRST=true
while IFS= read -r name; do
    [ -z "$name" ] && continue

    # Skip non-image
    [[ "$name" == *.json ]] && continue

    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        echo "," >> "$WALLPAPER_DIR/releases-manifest.json"
    fi

    # Key: filename without thumb- prefix
    key="$name"
    if [[ "$name" == thumb-* ]]; then
        key="thumbs/${name#thumb-}"
    fi

    printf '    "%s": "%s"' "$key" "$name" >> "$WALLPAPER_DIR/releases-manifest.json"

done <<< "$ASSETS"

cat >> "$WALLPAPER_DIR/releases-manifest.json" << 'EOF'

  }
}
EOF

echo -e "${GREEN}✅ Manifest saved${NC}"
exit 0
