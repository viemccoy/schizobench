#!/usr/bin/env python3
"""
Monitor for high-risk models that might timeout
Prepares retry commands with extended timeouts
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

# High-risk models that might need extended timeouts
HIGH_RISK_MODELS = [
    {
        "provider": "openai",
        "model": "o3-2025-04-16",
        "recommended_timeout_hours": 8,
        "reason": "Very large O-series model"
    },
    {
        "provider": "openai", 
        "model": "o1-2024-12-17",
        "recommended_timeout_hours": 6,
        "reason": "Large O-series model"
    },
    {
        "provider": "openrouter",
        "model": "meta-llama/llama-3.1-405b-instruct",
        "recommended_timeout_hours": 8,
        "reason": "405B parameter model"
    },
    {
        "provider": "openrouter",
        "model": "nousresearch/hermes-3-llama-3.1-405b",
        "recommended_timeout_hours": 8,
        "reason": "405B parameter model"
    }
]

def generate_retry_commands():
    """Generate retry commands for high-risk models"""
    
    print("High-Risk Model Retry Commands")
    print("=" * 70)
    print("\nIf any of these models timeout, use these commands:\n")
    
    for model_config in HIGH_RISK_MODELS:
        provider = model_config["provider"]
        model = model_config["model"]
        timeout = model_config["recommended_timeout_hours"]
        reason = model_config["reason"]
        
        print(f"\n# {model} ({reason})")
        print(f"# Recommended timeout: {timeout} hours")
        
        cmd = f"""timeout {timeout}h poetry run python run_benchmark_v3_robust.py \\
    --provider {provider} \\
    --model {model} \\
    --temperature {"1.0" if "o3" in model or "o1" in model else "0.7"} \\
    --scoring-provider openai \\
    --scoring-model gpt-4.1-2025-04-14"""
        
        print(cmd)
        print()
    
    # Also save to a shell script
    with open("retry_high_risk_models.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Auto-generated retry commands for high-risk models\n\n")
        
        for model_config in HIGH_RISK_MODELS:
            provider = model_config["provider"]
            model = model_config["model"]
            timeout = model_config["recommended_timeout_hours"]
            
            f.write(f"\n# Check if {model} needs retry\n")
            f.write(f"if ! ls results_v3/*{model.replace('/', '_')}*.json 2>/dev/null; then\n")
            f.write(f"    echo 'Retrying {model} with {timeout}h timeout...'\n")
            f.write(f"    timeout {timeout}h poetry run python run_benchmark_v3_robust.py \\\n")
            f.write(f"        --provider {provider} \\\n")
            f.write(f"        --model {model} \\\n")
            f.write(f"        --temperature {"1.0" if "o3" in model or "o1" in model else "0.7"} \\\n")
            f.write(f"        --scoring-provider openai \\\n")
            f.write(f"        --scoring-model gpt-4.1-2025-04-14\n")
            f.write(f"fi\n")
    
    print("\n✓ Commands saved to: retry_high_risk_models.sh")
    print("\nMonitor the overnight log for timeouts with:")
    print("grep -i 'timeout\\|failed' overnight_run_v3.log")

if __name__ == "__main__":
    generate_retry_commands()