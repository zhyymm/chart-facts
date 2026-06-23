#!/usr/bin/env bash
# Download Swiss Ephemeris ephemeris files for 1800–2399 AD.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/ephe"
BASE="https://www.astro.com/ftp/swisseph/ephe"

mkdir -p "${DEST}"

for file in sepl_18.se1 semo_18.se1; do
  if [[ -f "${DEST}/${file}" ]]; then
    echo "Already exists: ${DEST}/${file}"
    continue
  fi
  echo "Downloading ${file}..."
  curl -fsSL "${BASE}/${file}" -o "${DEST}/${file}"
done

echo "Done. Ephemeris files in ${DEST}"
