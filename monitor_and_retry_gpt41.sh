#!/bin/bash
# Monitor and retry GPT-4.1 when safe to do so

echo "GPT-4.1 Retry Monitor Started"
echo "============================="
echo ""

# Function to check if a model is running
is_running() {
    ps aux | grep -E "run_benchmark.*$1" | grep -v grep > /dev/null
    return $?
}

# Function to check if results exist
has_results() {
    ls results_v3/*gpt-4.1-2025-04-14*.json 2>/dev/null | grep -v mini > /dev/null
    return $?
}

# Wait for GPT-4.1-mini to finish
echo "Waiting for GPT-4.1-mini to complete..."
while is_running "gpt-4.1-mini"; do
    echo -n "."
    sleep 60
done
echo " Done!"

# Check if GPT-4.1 already has results
if has_results; then
    echo "✓ GPT-4.1 already has results. Exiting."
    exit 0
fi

# Wait a bit more to ensure clean state
echo "Waiting 30 seconds before starting GPT-4.1 retry..."
sleep 30

# Run GPT-4.1 with 6-hour timeout
echo ""
echo "Starting GPT-4.1 with 6-hour timeout..."
echo "======================================"

timeout 6h poetry run python run_benchmark_v3_robust.py \
    --provider openai \
    --model gpt-4.1-2025-04-14 \
    --temperature 0.7 \
    --scoring-provider openai \
    --scoring-model gpt-4.1-2025-04-14

if [ $? -eq 0 ]; then
    echo "✓ GPT-4.1 completed successfully!"
else
    echo "✗ GPT-4.1 failed or timed out after 4 hours"
fi