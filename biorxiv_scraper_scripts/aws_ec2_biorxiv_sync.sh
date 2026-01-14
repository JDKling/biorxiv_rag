#!/usr/bin/env bash
set -euo pipefail

# ---------- CONFIG ----------
REGION="us-east-1"
BUCKET="s3://biorxiv-src-monthly/Current_Content"
REQUESTER="--request-payer requester"

# Root workspace (adjust if you like)
ROOT="$HOME/biorxiv"
RAW="$ROOT/raw"
UNPACKED="$ROOT/unpacked"
XML="$ROOT/xml"
FILTERED="$ROOT/filtered"
LOGS="$ROOT/logs"

# Target categories
KEEP_CATEGORIES=(
  "Biochemistry"
  "Bioengineering"
  "Bioinformatics"
  "Biophysics"
  "Ecology"
  "Evolutionary biology"
  "Genetics"
  "Genomics"
  "Microbiology"
  "Molecular biology"
  "Plant biology"
  "Synthetic biology"
)
# ---------- CONFIG ----------

mkdir -p "$RAW" "$UNPACKED" "$XML" "$FILTERED" "$LOGS"

# Convert categories to repeated --keep args
KEEP_ARGS=()
for c in "${KEEP_CATEGORIES[@]}"; do
  KEEP_ARGS+=(--keep "$c")
done

# Get month folders from S3 (e.g., April_2025/)
echo "[INFO] Listing months from $BUCKET ..."
MONTHS=$(aws s3 ls "$BUCKET/" --region "$REGION" $REQUESTER \
  | awk '/PRE/ {print $2}' \
  | sed 's:/$::' )

if [[ -z "${MONTHS// }" ]]; then
  echo "[WARN] No month folders found. Check bucket/permissions."
  exit 0
fi

# Helper: unpack all .meca under a single month's RAW into UNPACKED
unpack_month() {
  local month="$1"
  local raw_month="$RAW/$month"
  local unpack_month="$UNPACKED/$month"

  echo "[INFO] Unpacking .meca for $month ..."
  echo "[DEBUG] raw_month=$raw_month"
  echo "[DEBUG] unpack_month=$unpack_month"
  local processed=0
  local skipped=0
  local total_files=$(find "$raw_month" -type f -name '*.meca' | wc -l)
  echo "[INFO] Found $total_files .meca files to process"
  
  # Find every .meca under raw/month, preserve relative structure into UNPACKED/month
  echo "[DEBUG] Starting while loop to process files..."
  echo "[DEBUG] Find command: find '$raw_month' -type f -name '*.meca' -print0"
  local current=0
  while IFS= read -r -d '' f; do
    echo "[DEBUG] Processing file: $f"
    current=$((current + 1))
    echo "[DEBUG] Current count: $current"
    rel="${f#$raw_month/}"             # path under raw/month
    echo "[DEBUG] Relative path: $rel"
    out="$unpack_month/${rel%.meca}"   # drop .meca
    echo "[DEBUG] Output path: $out"
    echo "[DEBUG] Creating directory: $(dirname "$out")"
    mkdir -p "$(dirname "$out")"
    echo "[DEBUG] Directory created successfully"

    if [[ -f "$out" ]] || [[ -d "$out" ]]; then
      echo "[SKIP] $out already exists and is not empty."
      skipped=$((skipped + 1))
      continue
    fi
    
    local file_size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo "unknown")
    echo "[INFO] [$current/$total_files] Extracting: $f (${file_size} bytes)"
    echo "[DEBUG] Creating output directory: $out"
    echo "[DEBUG] Starting unzip with 60s timeout..."
    # Use timeout and redirect stdin to prevent hanging on prompts
    if ! timeout 10 unzip -o -q "$f" -d "$out" < /dev/null 2>&1; then
      echo "[ERROR] Failed to extract: $f"
      echo "[ERROR] File may be corrupted, incomplete, or extraction timed out. Skipping..."
      rm -rf "$out"  # Clean up any partial extraction
      skipped=$((skipped + 1))
      continue
    fi
    echo "[SUCCESS] Extracted: $f"
    
    # Check if the unzipped directory is empty (indicates corrupted/invalid .meca)
    if [[ ! -d "$out" ]] || [[ -z "$(find "$out" -mindepth 1 -print -quit)" ]]; then
      echo "[ERROR] Empty extraction from: $f"
      echo "[ERROR] This indicates a corrupted or invalid .meca file. Skipping..."
      rm -rf "$out"  # Clean up empty directory
      skipped=$((skipped + 1))
      continue
    fi
    
    processed=$((processed + 1))
  done < <(find "$raw_month" -type f -name '*.meca' -print0)
  
  echo "[DEBUG] While loop completed"
  echo "[INFO] Unpacking complete for $month: $processed processed, $skipped skipped"
}

copy_xml() {
  local month="$1"
  local raw_month="$RAW/$month"
  local unpack_month="$UNPACKED/$month"
  local xml_month="$XML/$month"

  echo "[INFO] Copying XML files for $month ..."
  mkdir -p "$xml_month"
  find "$unpack_month" -type f -path '*/content/*.xml' -print0 | xargs -0 -I {} sh -c 'uuid=$(basename "$(dirname "$(dirname "{}")")") && echo "[INFO] {} --> '"$xml_month"'/$uuid.xml" && cp "{}" "'"$xml_month"'/$uuid.xml"'
  echo "[INFO] XML files copied for $month"

  # Now need to remove non-xml files from the xml_month directory
  echo "[INFO] Removing non-xml files from $xml_month ..."
  find "$xml_month" -type f -name '*.pdf' -print0 | xargs -0 -I {} sh -c 'echo "[INFO] Removing pdf file: {}" && rm -rf "{}"'
  find "$xml_month" -type f -name '*.tif' -print0 | xargs -0 -I {} sh -c 'echo "[INFO] Removing tif files: {}" && rm -rf "{}"'
  find "$xml_month" -type f -name '*.tiff' -print0 | xargs -0 -I {} sh -c 'echo "[INFO] Removing tiff files: {}" && rm -rf "{}"'
  find "$xml_month" -type d -name '*supplement*' -print0 | xargs -0 -I {} sh -c 'echo "[INFO] Removing supplement files: {}" && rm -rf "{}"'
}

# Process each month in order
for month in $MONTHS; do
  # Skip months that already have a .DONE marker
  if [[ -f "$FILTERED/$month/.DONE" ]]; then
    echo "[SKIP] $month already processed."
    continue
  fi

  echo "====================  $month  ===================="

  raw_month="$RAW/$month"
  unpack_month="$UNPACKED/$month"
  xml_month="$XML/$month"
  filt_month="$FILTERED/$month"
  mkdir -p "$raw_month" "$unpack_month" "$filt_month"

  echo "[INFO] Syncing $BUCKET/$month/ -> $raw_month"
  if ! aws s3 sync "$BUCKET/$month/" "$raw_month" --region "$REGION" $REQUESTER; then
    echo "[ERROR] aws s3 sync failed for $month; continuing to next month."
    continue
  fi

  # Check for .meca files with better error handling
  meca_count=$(find "$raw_month" -type f -name '*.meca' 2>/dev/null | wc -l)
  if [[ $meca_count -eq 0 ]]; then
    echo "[INFO] No .meca files found for $month. STOPPING!d"
    exit 1
  fi

  # Unpack every .meca for this month
  unpack_month "$month"
  unzip_count=$(find "$unpack_month" -type f -name '*' 2>/dev/null | wc -l)
  if [[ $unzip_count -eq 0 ]]; then
    echo "[ERROR] No files found in $unpack_month. STOPPING!"
    exit 1
  fi

  # Copy XML files for this month
  copy_xml "$month"
  xml_count=$(find "$xml_month" -type f -name '*.xml' 2>/dev/null | wc -l)
  if [[ $xml_count -eq 0 ]]; then
    echo "[ERROR] No XML files found in $xml_month. STOPPING!"
    exit 1
  fi

  # Run the Python filter against UNPACKED/month -> FILTERED/month
  echo "[INFO] Filtering $month ..."
  if ! python3 "$ROOT/filter_meca_by_category.py" \
       --root "$xml_month" \
       --out "$filt_month" \
       --logs "$LOGS" \
       "${KEEP_ARGS[@]}"; then
    echo "[ERROR] Filter script failed for $month; leaving files for debugging."
    continue
  fi

  # Cleanup to save space: remove RAW and UNPACKED for this month
  echo "[INFO] Cleanup $month (raw + unpacked) ..."
  rm -rf "$raw_month" "$unpack_month"

  # Mark month as done
  touch "$filt_month/.DONE"
  echo "[DONE] $month"
done

echo "[ALL DONE] Filtered content under: $FILTERED"
