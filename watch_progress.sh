#!/bin/bash
# Watch benchmark progress in real-time

cd /mnt/c/Users/vie/documents/schizobench

echo "Watching benchmark progress..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=========================================="
    echo "SchizoBench Progress Monitor"
    echo "Time: $(date)"
    echo "=========================================="
    
    # Check main process
    if pgrep -f "run_overnight.py" > /dev/null; then
        echo "✓ Main benchmark running"
    else
        echo "✗ Main benchmark not running!"
    fi
    
    # Check subprocess
    SUBPROCESS=$(ps aux | grep "run_benchmark_v3_improved.py" | grep -v grep | head -1)
    if [ ! -z "$SUBPROCESS" ]; then
        MODEL=$(echo "$SUBPROCESS" | grep -oP '(?<=--model )[^ ]+')
        echo "✓ Testing model: $MODEL"
    else
        echo "⏸ No model currently being tested"
    fi
    
    echo ""
    echo "Recent activity:"
    tail -10 overnight_*.log 2>/dev/null | grep -v "^$"
    
    echo ""
    echo "Result files:"
    NEW_FILES=$(find results_v3 -name "*.json" -mmin -60 2>/dev/null | wc -l)
    echo "New results in last hour: $NEW_FILES"
    
    sleep 10
done