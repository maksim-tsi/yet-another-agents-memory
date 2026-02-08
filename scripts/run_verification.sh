#!/bin/bash
set -e

# Start wrappers in background
echo "Starting wrappers..."
./scripts/start_benchmark_wrappers.sh > logs/verification_wrappers.log 2>&1 &
WRAPPER_PID=$!

# Wait for wrappers to be healthy
echo "Waiting for wrappers (pid $WRAPPER_PID) to initialize..."
# Simple wait loop checking logs or just failing if run_benchmark fails
# better: wait for port 8080 to be open
for i in {1..30}; do
    if curl -s http://localhost:8080/health | grep "ok" > /dev/null; then
        echo "Wrappers are ready."
        break
    fi
    sleep 2
    echo "Waiting..."
done

# Run Benchmark
echo "Running verification benchmark..."
export GOOGLE_API_KEY=$(grep GOOGLE_API_KEY .env | cut -d '=' -f2)
cd benchmarks/goodai-ltm-benchmark
export PYTHONPATH=$PYTHONPATH:$(pwd)
poetry run python runner/run_benchmark.py --configuration configurations/mas_verification_run.yml --agent-name mas-full

# Cleanup
echo "Stopping wrappers..."
kill $WRAPPER_PID
