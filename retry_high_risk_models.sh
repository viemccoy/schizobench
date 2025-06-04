#!/bin/bash
# Auto-generated retry commands for high-risk models


# Check if o3-2025-04-16 needs retry
if ! ls results_v3/*o3-2025-04-16*.json 2>/dev/null; then
    echo 'Retrying o3-2025-04-16 with 8h timeout...'
    timeout 8h poetry run python run_benchmark_v3_robust.py \
        --provider openai \
        --model o3-2025-04-16 \
        --temperature 1.0 \
        --scoring-provider openai \
        --scoring-model gpt-4.1-2025-04-14
fi

# Check if o1-2024-12-17 needs retry
if ! ls results_v3/*o1-2024-12-17*.json 2>/dev/null; then
    echo 'Retrying o1-2024-12-17 with 6h timeout...'
    timeout 6h poetry run python run_benchmark_v3_robust.py \
        --provider openai \
        --model o1-2024-12-17 \
        --temperature 1.0 \
        --scoring-provider openai \
        --scoring-model gpt-4.1-2025-04-14
fi

# Check if meta-llama/llama-3.1-405b-instruct needs retry
if ! ls results_v3/*meta-llama_llama-3.1-405b-instruct*.json 2>/dev/null; then
    echo 'Retrying meta-llama/llama-3.1-405b-instruct with 8h timeout...'
    timeout 8h poetry run python run_benchmark_v3_robust.py \
        --provider openrouter \
        --model meta-llama/llama-3.1-405b-instruct \
        --temperature 0.7 \
        --scoring-provider openai \
        --scoring-model gpt-4.1-2025-04-14
fi

# Check if nousresearch/hermes-3-llama-3.1-405b needs retry
if ! ls results_v3/*nousresearch_hermes-3-llama-3.1-405b*.json 2>/dev/null; then
    echo 'Retrying nousresearch/hermes-3-llama-3.1-405b with 8h timeout...'
    timeout 8h poetry run python run_benchmark_v3_robust.py \
        --provider openrouter \
        --model nousresearch/hermes-3-llama-3.1-405b \
        --temperature 0.7 \
        --scoring-provider openai \
        --scoring-model gpt-4.1-2025-04-14
fi
