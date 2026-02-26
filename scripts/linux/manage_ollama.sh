#!/usr/bin/env bash
# manage_ollama.sh — Kill and restart the Ollama server.
# Usage:
#   bash scripts/linux/manage_ollama.sh            # smart start/restart
#   bash scripts/linux/manage_ollama.sh stop
#   bash scripts/linux/manage_ollama.sh start
#   bash scripts/linux/manage_ollama.sh restart

set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

ACTION="${1:-auto}"

stop_ollama() {
    echo "  Stopping Ollama ..."
    pkill -9 -f "ollama serve"  2>/dev/null || true
    pkill -9 -f "ollama_llama"  2>/dev/null || true
    sleep 1
    echo "  Ollama stopped."
}

start_ollama() {
    echo "  Starting Ollama ..."
    nohup ollama serve >/dev/null 2>&1 &
    printf "  Waiting for Ollama to be ready"
    for i in $(seq 1 15); do
        sleep 1
        printf "."
        if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
            echo "  ready"
            echo "  Ollama is ready."
            return 0
        fi
    done
    echo ""
    echo "  WARNING: Ollama did not respond in time. Check 'ollama serve' manually." >&2
    return 1
}

is_running() {
    curl -sf --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1
}

echo ""
echo "  AI Training Hub — Ollama Manager"
echo ""

case "$ACTION" in
    stop)
        stop_ollama ;;
    start)
        if is_running; then
            echo "  Ollama already running."
        else
            start_ollama
        fi ;;
    restart)
        stop_ollama
        start_ollama ;;
    auto|*)
        if is_running; then
            echo "  Ollama detected — restarting for clean state ..."
            stop_ollama
            start_ollama
        else
            start_ollama
        fi ;;
esac

echo ""
