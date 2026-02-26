#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi


ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

ensure_ollama_linux() {
  if command -v ollama >/dev/null 2>&1; then return 0; fi
  echo "[ollama] not found -> installing..."
  # Official install script
  curl -fsSL https://ollama.com/install.sh | sh
}

ensure_ollama_running() {
  # Fast check: ollama list hits the local daemon
  if ollama list >/dev/null 2>&1; then return 0; fi

  # Try systemd service (if present)
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl start ollama >/dev/null 2>&1 || true
    sleep 1
    if ollama list >/dev/null 2>&1; then return 0; fi
  fi

  # Fallback: run serve in background
  echo "[ollama] starting daemon (fallback: nohup ollama serve)..."
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  sleep 2
  ollama list >/dev/null 2>&1
}

# Extract base models from Modelfiles (FROM line), and custom model names
scan_modelfiles() {
  # Prints: "<custom_name>\t<modelfile_path>\t<from_model>"
  find "$ROOT" -type f -name Modelfile \
    -not -path "*/.git/*" \
    -not -path "*/.venv/*" \
    -print0 | while IFS= read -r -d '' mf; do
      dir="$(dirname "$mf")"
      name="$(basename "$dir")"

      # Optional override: "# NAME: <modelname>"
      override="$(grep -E '^\s*#\s*NAME:\s*' "$mf" | head -n1 | sed -E 's/^\s*#\s*NAME:\s*//')"
      if [[ -n "${override:-}" ]]; then name="$override"; fi

      from="$(grep -E '^\s*FROM\s+' "$mf" | head -n1 | awk '{print $2}')"
      printf "%s\t%s\t%s\n" "$name" "$mf" "${from:-}"
    done
}

main() {
  ensure_ollama_linux
  ensure_ollama_running

  echo "[ollama] scanning for Modelfiles..."
  mapfile -t rows < <(scan_modelfiles || true)

  if [[ "${#rows[@]}" -eq 0 ]]; then
    echo "[ollama] No Modelfiles found in repo. (Nothing to graft.)"
    echo "[ollama] Tip: place custom Modelfiles under e.g. ollama/custom/<name>/Modelfile"
    exit 0
  fi

  # Pull FROM models first
  echo "[ollama] pulling base models referenced by FROM..."
  for r in "${rows[@]}"; do
    IFS=$'\t' read -r name mf from <<<"$r"
    if [[ -n "${from:-}" ]]; then
      echo "  -> ollama pull $from"
      ollama pull "$from"
    fi
  done

  # Create custom models
  echo "[ollama] creating custom models from Modelfiles..."
  for r in "${rows[@]}"; do
    IFS=$'\t' read -r name mf from <<<"$r"
    echo "  -> ollama create $name -f $mf"
    ollama create "$name" -f "$mf"
  done

  echo "[ollama] done. Installed models:"
  ollama list
}

main "$@"
