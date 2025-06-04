#!/usr/bin/env python3
"""
Quick benchmark status check - lightweight version
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
import re

def get_status():
    # Count completed
    results_dir = Path("results_v3")
    completed = len(list(results_dir.glob("schizobench_v3_*.json")))
    
    # Get current model
    ps_output = subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
    current_model = "None"
    
    for line in ps_output.split('\n'):
        if 'run_benchmark_v3_robust.py' in line and 'grep' not in line:
            match = re.search(r'--model\s+(\S+)', line)
            if match:
                current_model = match.group(1)
                break
    
    # Get current sequence
    try:
        log_tail = subprocess.run(
            ["tail", "-50", "overnight_run_v3.log"],
            capture_output=True,
            text=True
        ).stdout
        
        progress_matches = re.findall(r'PROGRESS:\s*(\d+)/(\d+)', log_tail)
        if progress_matches:
            current, total = progress_matches[-1]
            sequence_progress = f"{current}/{total}"
        else:
            sequence_progress = "Starting..."
    except:
        sequence_progress = "Unknown"
    
    # Print status
    print(f"\n📊 SchizoBench Status @ {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    print(f"✅ Completed: {completed}/38 models")
    print(f"🔄 Running: {current_model}")
    print(f"📍 Progress: {sequence_progress} sequences")
    
    # Check retry status
    if Path("gpt41_retry_v2.log").exists():
        retry_status = subprocess.run(
            ["tail", "-1", "gpt41_retry_v2.log"],
            capture_output=True,
            text=True
        ).stdout.strip()
        if "Waiting" in retry_status:
            print(f"⏳ GPT-4.1 retry: Waiting for current model")
        elif "Starting" in retry_status:
            print(f"🔄 GPT-4.1 retry: Running with 6h timeout")
    
    print("=" * 50)
    print(f"💡 Full monitor: poetry run python monitor_benchmark_progress.py")

if __name__ == "__main__":
    get_status()