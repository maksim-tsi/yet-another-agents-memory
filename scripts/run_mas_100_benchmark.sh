#!/bin/bash
set -e

# =================================================================================================
# MAS Memory Layer - Mixed 100-Question Parallel Benchmark Script
# =================================================================================================

# 1. Load Environment Variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found!"
    exit 1
fi

PYTHONPATH=$(pwd):$(pwd)/benchmarks/goodai-ltm-benchmark
export PYTHONPATH

# 2. Pre-flight Checks
echo "================================================================="
echo "Starting Pre-flight Checks..."
echo "================================================================="
echo "Checking Wrappers..."
./scripts/start_benchmark_wrappers.sh &
WRAPPER_PID=$!

# Wait for wrappers to be ready
echo "Waiting for wrappers to initialize..."
sleep 10

# 3. Define Run Parameters
CONFIG_FILE="./configurations/mas_mixed_100.yml"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_NAME_BASE="MAS Mixed 100 Run"

# 4. Start Benchmarks in Parallel
echo "================================================================="
echo "Starting Parallel Benchmarks..."
echo "================================================================="

# Function to calculate log filenames
get_log_file() {
    echo "logs/run_mas_100_${1}_${TIMESTAMP}.log"
}

# Gemini
AGENT="gemini"
LOG_FILE=$(get_log_file $AGENT)
RUN_NAME="${RUN_NAME_BASE} - ${AGENT} - ${TIMESTAMP}"
echo "Starting ${AGENT}..."
echo "  > Log: ${LOG_FILE}"
python3 benchmarks/goodai-ltm-benchmark/runner/run_benchmark.py \
    --configuration "${CONFIG_FILE}" \
    --agent-name "${AGENT}" \
    --run-name "${RUN_NAME}" \
    -y \
    > "${LOG_FILE}" 2>&1 &
PID_GEMINI=$!
echo "  > PID: ${PID_GEMINI}"

# MAS Full
AGENT="mas-full"
LOG_FILE=$(get_log_file $AGENT)
RUN_NAME="${RUN_NAME_BASE} - ${AGENT} - ${TIMESTAMP}"
echo "Starting ${AGENT}..."
echo "  > Log: ${LOG_FILE}"
python3 benchmarks/goodai-ltm-benchmark/runner/run_benchmark.py \
    --configuration "${CONFIG_FILE}" \
    --agent-name "${AGENT}" \
    --run-name "${RUN_NAME}" \
    -y \
    > "${LOG_FILE}" 2>&1 &
PID_FULL=$!
echo "  > PID: ${PID_FULL}"

# MAS RAG
AGENT="mas-rag"
LOG_FILE=$(get_log_file $AGENT)
RUN_NAME="${RUN_NAME_BASE} - ${AGENT} - ${TIMESTAMP}"
echo "Starting ${AGENT}..."
echo "  > Log: ${LOG_FILE}"
python3 benchmarks/goodai-ltm-benchmark/runner/run_benchmark.py \
    --configuration "${CONFIG_FILE}" \
    --agent-name "${AGENT}" \
    --run-name "${RUN_NAME}" \
    -y \
    > "${LOG_FILE}" 2>&1 &
PID_RAG=$!
echo "  > PID: ${PID_RAG}"

# MAS Full Context
AGENT="mas-full-context"
LOG_FILE=$(get_log_file $AGENT)
RUN_NAME="${RUN_NAME_BASE} - ${AGENT} - ${TIMESTAMP}"
echo "Starting ${AGENT}..."
echo "  > Log: ${LOG_FILE}"
python3 benchmarks/goodai-ltm-benchmark/runner/run_benchmark.py \
    --configuration "${CONFIG_FILE}" \
    --agent-name "${AGENT}" \
    --run-name "${RUN_NAME}" \
    -y \
    > "${LOG_FILE}" 2>&1 &
PID_CONTEXT=$!
echo "  > PID: ${PID_CONTEXT}"

echo "All benchmarks started."
echo "Waiting for completion..."

# 5. Wait for all processes
wait $PID_GEMINI
echo "Gemini Benchmark Finished."

wait $PID_FULL
echo "MAS Full Benchmark Finished."

wait $PID_RAG
echo "MAS RAG Benchmark Finished."

wait $PID_CONTEXT
echo "MAS Full Context Benchmark Finished."

echo "================================================================="
echo "All Benchmarks Completed."
echo "Check logs in logs/ directory."
echo "================================================================="
