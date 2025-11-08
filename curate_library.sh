#!/bin/bash
# Automated Library Curation Script
# Builds large, high-quality image libraries without intervention

echo "============================================================"
echo "Intelligent Image Library Curation"
echo "============================================================"
echo ""

# Configuration
MIN_QUALITY=70
IMAGES_PER_THEME=25
OUTPUT_DIR="curated_collections"

# Categories to curate (customize this list)
CATEGORIES=(
    "nature"
    "urban"
    "abstract"
    "lifestyle"
    "technology"
)

echo "Configuration:"
echo "  Min Quality: $MIN_QUALITY/100"
echo "  Images per Theme: $IMAGES_PER_THEME"
echo "  Output: $OUTPUT_DIR"
echo "  Categories: ${CATEGORIES[@]}"
echo ""
echo "============================================================"
echo ""

# Check if curator.py exists
if [ ! -f "curator.py" ]; then
    echo "❌ Error: curator.py not found in current directory"
    exit 1
fi

# Process each category
for category in "${CATEGORIES[@]}"; do
    echo ""
    echo "🎨 Starting curation: $category"
    echo "------------------------------------------------------------"

    python curator.py "$category" \
        --images-per-theme "$IMAGES_PER_THEME" \
        --min-quality "$MIN_QUALITY" \
        --output "$OUTPUT_DIR"

    if [ $? -eq 0 ]; then
        echo "✅ Completed: $category"
    else
        echo "❌ Failed: $category"
    fi

    # Pause between categories (respectful to APIs)
    echo "⏸️  Pausing 10 seconds before next category..."
    sleep 10
done

echo ""
echo "============================================================"
echo "✅ Library curation complete!"
echo "============================================================"
echo "📁 Output location: $OUTPUT_DIR"
echo ""
echo "Summary by category:"
for category in "${CATEGORIES[@]}"; do
    latest_dir=$(ls -td "$OUTPUT_DIR/$category"/*/ 2>/dev/null | head -1)
    if [ -d "$latest_dir" ]; then
        excellent_count=$(find "$latest_dir/excellent" -name "*.jpg" 2>/dev/null | wc -l)
        good_count=$(find "$latest_dir/good" -name "*.jpg" 2>/dev/null | wc -l)
        acceptable_count=$(find "$latest_dir/acceptable" -name "*.jpg" 2>/dev/null | wc -l)
        total=$((excellent_count + good_count + acceptable_count))

        echo "  $category: $total images ($excellent_count excellent, $good_count good, $acceptable_count acceptable)"
    fi
done
echo ""
