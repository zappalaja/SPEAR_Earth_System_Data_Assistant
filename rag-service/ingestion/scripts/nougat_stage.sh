#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 path/to/nougat_stage.conf"
  exit 1
fi

CONF="$1"
if [[ ! -f "$CONF" ]]; then
  echo "Config not found: $CONF"
  exit 1
fi

# shellcheck disable=SC1090
source "$CONF"

mkdir -p "$NOUGAT_OUT_DIR" "$MERGED_MD_DIR" "$LOG_DIR"

# --- Activate conda env (robust) ---
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
  echo "Could not find conda.sh. Please ensure conda is installed."
  exit 1
fi

conda activate "$CONDA_ENV"

echo "Using conda env: $CONDA_ENV"
echo "PDFs:        $INPUT_PDF_DIR"
echo "Nougat out:  $NOUGAT_OUT_DIR"
echo "Merged md:   $MERGED_MD_DIR"
echo "Logs:        $LOG_DIR"
echo

shopt -s nullglob
PDFS=("$INPUT_PDF_DIR"/*.pdf)
if [[ ${#PDFS[@]} -eq 0 ]]; then
  echo "No PDFs found in: $INPUT_PDF_DIR"
  exit 1
fi

OK=0
FAIL=0

for pdf in "${PDFS[@]}"; do
  base="$(basename "$pdf")"
  stem="${base%.pdf}"
  log="$LOG_DIR/${stem}.nougat.log"

  echo "Running Nougat on: $base"
  set +e
  nougat "$pdf" --out "$NOUGAT_OUT_DIR" $NOUCAT_EXTRA_ARGS >"$log" 2>&1
  rc=$?
  set -e

  if [[ $rc -eq 0 ]]; then
    OK=$((OK+1))
  else
    FAIL=$((FAIL+1))
    echo "  FAILED: $base (see $log)"
    tail -n 10 "$log" || true
  fi
done

echo
echo "Nougat runs: ok=$OK, failed=$FAIL"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MERGER="$SCRIPT_DIR/merge_nougat_md.py"

if [[ ! -f "$MERGER" ]]; then
  echo "merge_nougat_md.py not found next to this script. Expected: $MERGER"
  exit 1
fi

python "$MERGER" --pdf_dir "$INPUT_PDF_DIR" --nougat_out "$NOUGAT_OUT_DIR" --merged_out "$MERGED_MD_DIR"
echo "Done."
