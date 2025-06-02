#!/bin/bash
# Monitor SchizoBench benchmark progress

cd /mnt/c/Users/vie/documents/schizobench

echo "=========================================="
echo "SchizoBench Benchmark Monitor"
echo "=========================================="
echo ""

# Find the latest log file
LOG_FILE=$(ls -t overnight_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "No benchmark log file found!"
    exit 1
fi

echo "Monitoring: $LOG_FILE"
echo ""

# Check if process is running
PID=$(pgrep -f "python run_overnight.py")
if [ -z "$PID" ]; then
    echo "⚠️  Benchmark is not currently running!"
else
    echo "✓ Benchmark is running (PID: $PID)"
fi

echo ""
echo "Current Progress:"
echo "-----------------"

# Show progress
grep -E "(Model [0-9]+/[0-9]+|Successfully completed|Failed|Partial results)" "$LOG_FILE" | tail -20

echo ""
echo "Recent Activity:"
echo "----------------"
tail -10 "$LOG_FILE"

echo ""
echo "To see full log: tail -f $LOG_FILE"