#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

for CITY in dc sf; do
  INPUT="../static/data/${CITY}_districts.geojson"
  MBTILES="../static/data/${CITY}_districts.mbtiles"
  PMTILES="../static/data/${CITY}_districts.pmtiles"

  echo "Converting ${INPUT} -> ${PMTILES}"

  tippecanoe \
    --force \
    --output="${MBTILES}" \
    --layer="districts" \
    --minimum-zoom=0 \
    --maximum-zoom=14 \
    --no-feature-limit \
    --no-tile-size-limit \
    --drop-densest-as-needed \
    --read-parallel \
    "${INPUT}"

  npx pmtiles convert "${MBTILES}" "${PMTILES}"

  rm -f "${MBTILES}"
  echo "Created ${PMTILES}"
  echo
done
