#!/usr/bin/env python3
"""
Retry GPT-4.1 with extended timeout
Run this in parallel with the ongoing benchmark
"""

import subprocess
import time
from pathlib import Path
import json
import sys

def check_if_already_completed(model_name):
    """Check if model already has results"""
    results_dir = Path("results_v3")
    for json_file in results_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            try:
                data = json.load(f)
                if data['metadata']['model'] == model_name:
                    return True
            except:
                pass
    return False

def wait_for_current_benchmark():
    """Wait for any current benchmark of the same model to finish"""
    while True:
        # Check if any benchmark process is running for gpt-4.1-2025-04-14
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        if "gpt-4.1-2025-04-14" in result.stdout and "run_benchmark" in result.stdout:
            print("Waiting for current GPT-4.1 benchmark to finish...")
            time.sleep(60)  # Check every minute
        else:
            break

def run_gpt41_with_extended_timeout():
    """Run GPT-4.1 with 4-hour timeout"""
    
    model = "gpt-4.1-2025-04-14"
    
    # First check if it already completed
    if check_if_already_completed(model):
        print(f"✓ {model} already completed!")
        return True
    
    # Wait for any current instance to finish
    wait_for_current_benchmark()
    
    print(f"\n{'='*70}")
    print(f"Starting GPT-4.1 retry with 4-hour timeout")
    print(f"Model: {model}")
    print(f"{'='*70}\n")
    
    # Run with extended timeout
    cmd = [
        "poetry", "run", "python", "run_benchmark_v3_robust.py",
        "--provider", "openai",
        "--model", model,
        "--temperature", "0.7",
        "--scoring-provider", "openai",
        "--scoring-model", "gpt-4.1-2025-04-14"
    ]
    
    try:
        # 4 hour timeout = 14400 seconds
        process = subprocess.run(
            cmd,
            timeout=14400,  # 4 hours
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            print(f"✓ Successfully completed {model}")
            return True
        else:
            print(f"✗ Failed with return code {process.returncode}")
            print(f"Error: {process.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timed out after 4 hours!")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("GPT-4.1 Extended Timeout Retry Script")
    print("=====================================\n")
    
    # Add a small delay to avoid conflicts
    print("Waiting 30 seconds before starting...")
    time.sleep(30)
    
    success = run_gpt41_with_extended_timeout()
    
    if success:
        print("\n✓ GPT-4.1 completed successfully!")
        print("Check results_v3/ for the output file")
    else:
        print("\n✗ GPT-4.1 failed even with extended timeout")
        print("Consider running manually with even longer timeout")
    
    sys.exit(0 if success else 1)