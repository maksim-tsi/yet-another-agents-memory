#!/bin/bash

# Script: diagnose_benchmark.sh
# Purpose: Run a minimal MAS benchmark and validate wrapper connectivity.
# Usage: ./diagnose_benchmark.sh

set -e
set -u
set -o pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BENCHMARK_ROOT="$PROJECT_ROOT/benchmarks/goodai-ltm-benchmark"
ENV_FILE="$PROJECT_ROOT/.env"

PYTHON="$PROJECT_ROOT/.venv/bin/python"

function check_prerequisites() {
    if [ ! -f "$PYTHON" ]; then
        echo -e "${RED}❌ Error: .venv not found at $PYTHON${NC}"
        echo "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
        exit 1
    fi

    if [ -z "${GOOGLE_API_KEY:-}" ] && [ -f "$ENV_FILE" ]; then
        GOOGLE_API_KEY_VALUE="$(grep -E '^GOOGLE_API_KEY=' "$ENV_FILE" | head -n 1 | cut -d= -f2- | sed 's/[[:space:]]*#.*$//')"
        if [ -n "$GOOGLE_API_KEY_VALUE" ]; then
            export GOOGLE_API_KEY="$GOOGLE_API_KEY_VALUE"
            echo -e "${BLUE}ℹ️  Loaded GOOGLE_API_KEY from .env${NC}"
        fi
    fi

    if [ -z "${GOOGLE_API_KEY:-}" ]; then
        echo -e "${RED}❌ Error: GOOGLE_API_KEY is not set${NC}"
        echo "Export GOOGLE_API_KEY before running the benchmark."
        exit 1
    fi

    if command -v curl >/dev/null 2>&1; then
        if ! curl -sf "http://localhost:8080/health" >/dev/null; then
            echo -e "${RED}❌ Error: MAS wrapper is not reachable at http://localhost:8080${NC}"
            echo "Start the wrapper service before running this diagnostic."
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  Warning: curl not found; skipping wrapper health check${NC}"
    fi
}

function run_diagnostic() {
    echo -e "${BLUE}ℹ️  Running minimal benchmark (mas_single_test.yml)...${NC}"
    "$PYTHON" "$BENCHMARK_ROOT/run_benchmark.py" \
        -c "$BENCHMARK_ROOT/configurations/mas_single_test.yml" \
        -a gemini-2.5-flash-lite
    echo -e "${GREEN}✅ Benchmark diagnostic completed${NC}"
}

function summarize_wrapper_logs() {
    LOG_FILE="$PROJECT_ROOT/logs/wrapper_full.log"
    RATE_LOG_LATEST="$(ls -t "$PROJECT_ROOT"/logs/rate_limiter_*.jsonl 2>/dev/null | head -n 1 || true)"
    if [ -f "$LOG_FILE" ]; then
        RUN_TURN_COUNT="$(grep -c "run_turn" "$LOG_FILE" || true)"
        echo -e "${BLUE}ℹ️  Wrapper log run_turn count: $RUN_TURN_COUNT${NC}"
        echo -e "${BLUE}ℹ️  Wrapper log path: $LOG_FILE${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: Wrapper log not found at $LOG_FILE${NC}"
    fi

    if [ -n "$RATE_LOG_LATEST" ]; then
        LAST_RATE_ENTRY="$(tail -n 1 "$RATE_LOG_LATEST" 2>/dev/null || true)"
        echo -e "${BLUE}ℹ️  Rate limiter log: $RATE_LOG_LATEST${NC}"
        if [ -n "$LAST_RATE_ENTRY" ]; then
            echo -e "${BLUE}ℹ️  Latest rate limiter entry: $LAST_RATE_ENTRY${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Warning: No rate limiter logs found in logs/${NC}"
    fi
}

function main() {
    check_prerequisites
    run_diagnostic
    summarize_wrapper_logs
}

main "$@"
