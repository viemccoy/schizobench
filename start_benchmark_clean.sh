#!/bin/bash
# Start SchizoBench benchmark - Clean Run

cd /mnt/c/Users/vie/documents/schizobench

echo "=================================="
echo "SchizoBench v3.0 - Clean Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    exit 1
fi

# Verify environment loading
echo "Verifying environment..."
poetry run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
apis = {
    'ANTHROPIC': os.getenv('ANTHROPIC_API_KEY'),
    'OPENAI': os.getenv('OPENAI_API_KEY'), 
    'GOOGLE': os.getenv('GOOGLE_API_KEY'),
    'OPENROUTER': os.getenv('OPENROUTER_API_KEY')
}
missing = [k for k, v in apis.items() if not v]
if missing:
    print(f'ERROR: Missing API keys: {missing}')
    exit(1)
print('✓ All API keys loaded successfully')
"

if [ $? -ne 0 ]; then
    echo "Environment verification failed!"
    exit 1
fi

# Clean up old logs
echo ""
echo "Cleaning up old logs..."
mkdir -p benchmark_logs/archive
mv overnight_*.log benchmark_logs/archive/ 2>/dev/null || true

# Start the benchmark
LOG_FILE="overnight_$(date +%Y%m%d_%H%M%S).log"
echo ""
echo "Starting benchmark..."
echo "Log file: $LOG_FILE"
echo ""

nohup poetry run python run_overnight.py > "$LOG_FILE" 2>&1 &
PID=$!

echo "✓ Benchmark started with PID: $PID"
echo ""
echo "Commands:"
echo "  Monitor: ./monitor_benchmark.sh"
echo "  Live log: tail -f $LOG_FILE"
echo "  Stop: kill $PID"
echo ""
echo "Expected duration: 3-5 hours for 40 models"