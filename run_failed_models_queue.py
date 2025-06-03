#!/usr/bin/env python3
"""
Queue system for retrying failed models with extended timeouts
This can run in parallel with the main overnight benchmark
"""

import subprocess
import time
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import List, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('failed_models_retry.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Failed models queue with extended timeouts
RETRY_QUEUE = [
    {
        "provider": "openai",
        "model": "gpt-4.1-2025-04-14",
        "timeout_hours": 4,
        "reason": "Timed out after 2 hours"
    },
    # Add more failed models here as needed
]

def check_if_completed(provider: str, model_name: str) -> bool:
    """Check if model already has results"""
    results_dir = Path("results_v3")
    for json_file in results_dir.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if data['metadata']['model'] == model_name:
                    logger.info(f"✓ {provider}/{model_name} already has results")
                    return True
        except:
            pass
    return False

def is_model_running(model_name: str) -> bool:
    """Check if model is currently being benchmarked"""
    result = subprocess.run(
        ["ps", "aux"], 
        capture_output=True, 
        text=True
    )
    return model_name in result.stdout and "run_benchmark" in result.stdout

def wait_for_model_to_finish(model_name: str):
    """Wait for a specific model to finish running"""
    while is_model_running(model_name):
        logger.info(f"Waiting for {model_name} to finish current run...")
        time.sleep(60)

def run_model_with_timeout(config: Dict) -> bool:
    """Run a single model with specified timeout"""
    provider = config['provider']
    model = config['model']
    timeout_hours = config['timeout_hours']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Starting: {provider}/{model}")
    logger.info(f"Timeout: {timeout_hours} hours")
    logger.info(f"Reason for retry: {config.get('reason', 'Unknown')}")
    logger.info(f"{'='*70}\n")
    
    cmd = [
        "poetry", "run", "python", "run_benchmark_v3_robust.py",
        "--provider", provider,
        "--model", model,
        "--temperature", str(config.get('temperature', 0.7)),
        "--scoring-provider", "openai",
        "--scoring-model", "gpt-4.1-2025-04-14"
    ]
    
    # Add any special parameters
    if config.get('system_prompt'):
        cmd.extend(["--system-prompt", config['system_prompt']])
    
    try:
        timeout_seconds = timeout_hours * 3600
        process = subprocess.run(
            cmd,
            timeout=timeout_seconds,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            logger.info(f"✓ Successfully completed {provider}/{model}")
            return True
        else:
            logger.error(f"✗ Failed with return code {process.returncode}")
            if process.stderr:
                logger.error(f"Error: {process.stderr[:500]}...")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Timed out after {timeout_hours} hours!")
        return False
    except Exception as e:
        logger.error(f"✗ Exception: {e}")
        return False

def monitor_and_retry():
    """Main function to process retry queue"""
    logger.info("Failed Models Retry Queue Started")
    logger.info(f"Models in queue: {len(RETRY_QUEUE)}")
    
    completed = []
    failed = []
    
    for config in RETRY_QUEUE:
        provider = config['provider']
        model = config['model']
        
        # Skip if already completed
        if check_if_completed(provider, model):
            completed.append(f"{provider}/{model}")
            continue
        
        # Wait if currently running
        wait_for_model_to_finish(model)
        
        # Add a small delay between models
        time.sleep(10)
        
        # Run with extended timeout
        success = run_model_with_timeout(config)
        
        if success:
            completed.append(f"{provider}/{model}")
        else:
            failed.append(f"{provider}/{model}")
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("RETRY QUEUE SUMMARY")
    logger.info("="*70)
    logger.info(f"Total models: {len(RETRY_QUEUE)}")
    logger.info(f"Completed: {len(completed)}")
    logger.info(f"Failed: {len(failed)}")
    
    if completed:
        logger.info("\nCompleted models:")
        for m in completed:
            logger.info(f"  ✓ {m}")
    
    if failed:
        logger.info("\nFailed models (need manual intervention):")
        for m in failed:
            logger.info(f"  ✗ {m}")
    
    logger.info("\nCheck results_v3/ for output files")

if __name__ == "__main__":
    # Wait a bit to avoid conflicts with main runner
    logger.info("Starting in 60 seconds...")
    time.sleep(60)
    
    monitor_and_retry()