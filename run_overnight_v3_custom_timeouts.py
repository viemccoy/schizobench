#!/usr/bin/env python3
"""
Enhanced overnight runner with custom timeouts per model
Use this for future runs where you need specific timeout control
"""

import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Tuple, Optional
import sys

# Enhanced model configurations with custom timeouts
MODEL_CONFIGS = {
    "openai": [
        {"model": "gpt-4.1-2025-04-14", "timeout_hours": 6},  # 6 hours for GPT-4.1
        {"model": "gpt-4.1-mini-2025-04-14", "timeout_hours": 3},
        {"model": "gpt-4.1-nano-2025-04-14", "timeout_hours": 2},
        {"model": "gpt-4o-2024-08-06", "timeout_hours": 4},
        {"model": "gpt-4o-mini-2024-07-18", "timeout_hours": 2},
        {"model": "o3-2025-04-16", "temperature": 1.0, "timeout_hours": 8},  # 8 hours for O3
        {"model": "o3-mini-2025-01-31", "temperature": 1.0, "timeout_hours": 4},
        {"model": "o4-mini-2025-04-16", "temperature": 1.0, "timeout_hours": 4},
        {"model": "o1-2024-12-17", "temperature": 1.0, "timeout_hours": 6},
        {"model": "o1-mini-2024-09-12", "temperature": 1.0, "timeout_hours": 3},
    ],
    
    # Add other providers with custom timeouts as needed
}

# Copy the rest of the logic from run_overnight_v3.py but use timeout_hours from config
# This allows fine-grained control over each model's timeout

def run_single_benchmark_streaming(provider: str, config: Dict, retry_count: int = 0, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """Run benchmark with custom timeout"""
    
    model = config["model"]
    temperature = config.get("temperature", 0.7)
    timeout_hours = config.get("timeout_hours", 2)  # Default 2 hours if not specified
    
    print(f"\n{'='*70}")
    print(f"Starting: {provider}/{model}")
    print(f"Custom timeout: {timeout_hours} hours")
    print(f"{'='*70}\n")
    
    timeout_seconds = timeout_hours * 3600
    
    # Rest of implementation...
    # (Copy from run_overnight_v3.py but use timeout_seconds calculated above)

print("Custom Timeout Overnight Runner")
print("This script allows per-model timeout configuration")
print("Edit MODEL_CONFIGS to set specific timeouts for each model")