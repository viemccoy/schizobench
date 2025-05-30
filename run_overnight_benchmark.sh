#!/bin/bash
# Overnight SchizoBench Run Script
# This script runs all benchmarks with maximum robustness

# Set up logging
LOG_DIR="benchmark_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="${LOG_DIR}/overnight_run_${TIMESTAMP}.log"

# Ensure directories exist
mkdir -p $LOG_DIR
mkdir -p results_v3
mkdir -p results_comparison
mkdir -p dashboards

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MAIN_LOG"
}

# Start logging
log "Starting overnight SchizoBench benchmark run"
log "================================================================"

# Set environment variables for robustness
export PYTHONUNBUFFERED=1  # Ensure output is not buffered
export TOKENIZERS_PARALLELISM=false  # Avoid tokenizer warnings

# Check API keys
log "Checking API keys..."
if [ -z "$OPENAI_API_KEY" ]; then
    log "WARNING: OPENAI_API_KEY not set"
fi
if [ -z "$ANTHROPIC_API_KEY" ]; then
    log "WARNING: ANTHROPIC_API_KEY not set"
fi

# Run the benchmarks
log "Starting benchmark suite..."
log "Note: Individual model failures will not stop the overall run"
log "================================================================"

# Use nohup to prevent interruption if terminal closes
nohup python run_all_models.py >> "$MAIN_LOG" 2>&1 &
PID=$!

log "Benchmark started with PID: $PID"
log "You can monitor progress with: tail -f $MAIN_LOG"
log "Or check individual model logs in: $LOG_DIR/"

# Optional: Wait and generate dashboard
# If you want the script to wait and generate dashboard after completion:
# wait $PID
# log "Benchmarks complete. Generating dashboard..."
# python generate_v3_dashboard_enhanced.py >> "$MAIN_LOG" 2>&1
# log "Dashboard generation complete!"

log "================================================================"
log "Overnight benchmark launched successfully!"
log "Check results in the morning in:"
log "  - Individual logs: $LOG_DIR/"
log "  - Results: results_v3/"
log "  - Dashboard: dashboards/"
log "================================================================"