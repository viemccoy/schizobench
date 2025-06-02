#!/usr/bin/env python3
"""
Ultra-robust overnight benchmark runner with real-time output streaming
"""

import os
import sys
import time
import logging
import subprocess
import threading
from datetime import datetime
import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import select

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Setup logging
log_dir = Path("benchmark_logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"overnight_run_{timestamp}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Model configurations
MODEL_CONFIGS = {
    "anthropic": [
        {"model": "claude-opus-4-20250514", "slow": True},
        {"model": "claude-sonnet-4-20250514", "slow": True},
        {"model": "claude-3-7-sonnet-20250219", "slow": True},
        {"model": "claude-3-5-sonnet-20241022"},
        {"model": "claude-3-5-sonnet-20240620"},
        {"model": "claude-3-5-haiku-20241022"},
        {"model": "claude-3-opus-20240229", "slow": True},
        {"model": "claude-3-haiku-20240307"},
        {"model": "claude-opus-4-20250514", "slow": True, "enhanced_prompt": True, "label": "Claude Opus 4 (Enhanced)"},
    ],
    
    "openai": [
        {"model": "gpt-4.1-2025-04-14"},
        {"model": "gpt-4.1-mini-2025-04-14"},
        {"model": "gpt-4.1-nano-2025-04-14"},
        {"model": "gpt-4o-2024-08-06"},
        {"model": "gpt-4o-mini-2024-07-18"},
        {"model": "o3-2025-04-16", "temperature": 1.0, "slow": True},
        {"model": "o3-mini-2025-01-31", "temperature": 1.0},
        {"model": "o4-mini-2025-04-16", "temperature": 1.0},
        {"model": "o1-2024-12-17", "temperature": 1.0},
        {"model": "o1-mini-2024-09-12", "temperature": 1.0},
    ],
    
    "google": [
        {"model": "gemini-2.5-pro-preview-05-06"},
        {"model": "gemini-2.5-flash-preview-05-20"},
        {"model": "gemini-2.0-flash-exp"},
        {"model": "gemini-2.0-flash-lite"},
    ],
    
    "openrouter": [
        {"model": "deepseek/deepseek-r1-0528:free"},
        {"model": "deepseek/deepseek-chat-v3-0324:free"},
        {"model": "deepseek/deepseek-r1:free"},
        {"model": "deepseek/deepseek-chat:free"},
        {"model": "x-ai/grok-3-beta"},
        {"model": "x-ai/grok-3-mini-beta"},
        {"model": "x-ai/grok-2-1212"},
        {"model": "meta-llama/llama-4-maverick:free"},
        {"model": "meta-llama/llama-4-scout:free"},
        {"model": "meta-llama/llama-3.3-70b-instruct:free"},
        {"model": "meta-llama/llama-3.1-405b-instruct", "slow": True},
        {"model": "meta-llama/llama-3.1-70b-instruct"},
        {"model": "meta-llama/llama-3-70b-instruct"},
        {"model": "nousresearch/hermes-3-llama-3.1-70b"},
        {"model": "nousresearch/hermes-3-llama-3.1-405b", "slow": True},
    ]
}

def stream_subprocess_output(process, label: str):
    """Stream subprocess output in real-time"""
    while True:
        output = process.stdout.readline()
        if output:
            line = output.strip()
            if line:
                logger.info(f"[{label}] {line}")
                # Also print progress messages directly
                if "PROGRESS:" in line or "Evaluating:" in line:
                    print(f"  >>> {line}", flush=True)
        else:
            break

def run_single_benchmark_streaming(provider: str, config: Dict, retry_count: int = 0, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """Run benchmark with real-time output streaming"""
    
    model = config["model"]
    temperature = config.get("temperature", 0.7)
    enhanced_prompt = config.get("enhanced_prompt", False)
    label = config.get("label", f"{provider}/{model}")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Starting: {label}")
    logger.info(f"Attempt: {retry_count + 1}/{max_retries}")
    
    timeout_seconds = 14400 if config.get("slow", False) else 7200
    logger.info(f"Timeout: {timeout_seconds/3600:.1f} hours")
    
    try:
        # Build command - use the robust version
        cmd = [
            "poetry", "run", "python", "run_benchmark_v3_robust.py",
            "--provider", provider,
            "--model", model,
            "--temperature", str(temperature),
            "--scoring-provider", "openai",
            "--scoring-model", "gpt-4.1-2025-04-14"
        ]
        
        # Add enhanced prompt if needed
        if enhanced_prompt:
            enhanced_prompt_path = Path("archive/claude_system_prompt_enhanced.txt")
            if enhanced_prompt_path.exists():
                with open(enhanced_prompt_path, "r") as f:
                    prompt_content = f.read().strip()
                cmd.extend(["--system-prompt", prompt_content])
            else:
                logger.error(f"Enhanced prompt file not found")
                return False, "Enhanced prompt file missing"
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Start subprocess with real-time output
        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        
        # Stream output in a separate thread
        output_thread = threading.Thread(
            target=stream_subprocess_output,
            args=(process, label)
        )
        output_thread.start()
        
        # Wait for completion with timeout
        try:
            return_code = process.wait(timeout=timeout_seconds)
            output_thread.join()
            elapsed_time = time.time() - start_time
            
            if return_code == 0:
                logger.info(f"✓ Successfully completed {label} in {elapsed_time/60:.1f} minutes")
                return True, None
            else:
                error_msg = f"Process exited with code {return_code}"
                logger.warning(f"✗ Failed {label} - {error_msg}")
                
                # Check for partial results
                if check_partial_results(model):
                    logger.info(f"⚠ Partial results found for {label}")
                    return True, "Partial results"
                
                # Retry if needed
                if retry_count < max_retries - 1:
                    wait_time = 30 * (retry_count + 1)
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    return run_single_benchmark_streaming(provider, config, retry_count + 1, max_retries)
                
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ Timeout after {timeout_seconds/3600:.1f} hours for {label}")
            process.kill()
            output_thread.join()
            
            if check_partial_results(model):
                logger.info(f"⚠ Partial results found despite timeout")
                return True, "Timeout with partial results"
                
            return False, f"Timeout after {timeout_seconds/3600:.1f} hours"
            
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"✗ {error_msg} for {label}")
        logger.error(traceback.format_exc())
        return False, error_msg

def check_partial_results(model: str) -> bool:
    """Check if partial results exist for a model"""
    results_dir = Path("results_v3")
    if not results_dir.exists():
        return False
    
    model_str = model.replace(".", "-")
    for file in results_dir.glob("*.json"):
        if model_str in file.name:
            try:
                # Check file size and content
                if file.stat().st_size > 1000:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        # Check for actual results
                        if "sequences" in data and len(data.get("sequences", [])) > 5:
                            return True
                        elif "analysis" in data and data["analysis"].get("total_sequences", 0) > 5:
                            return True
            except:
                pass
    return False

def validate_environment() -> Dict[str, bool]:
    """Validate API keys and environment"""
    providers = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    
    available = {}
    logger.info("Checking API keys:")
    for provider, env_var in providers.items():
        if os.getenv(env_var):
            available[provider] = True
            logger.info(f"  ✓ {provider.capitalize()} API key found")
        else:
            available[provider] = False
            logger.warning(f"  ✗ {env_var} not set - {provider} models will be skipped")
    
    return available

def main():
    """Main overnight benchmark runner"""
    logger.info("="*70)
    logger.info("SchizoBench v3.0 Ultra-Robust Overnight Benchmark")
    logger.info("="*70)
    
    # Test that the benchmark script exists and is importable
    try:
        logger.info("Verifying benchmark script...")
        result = subprocess.run(
            ["poetry", "run", "python", "-c", "import run_benchmark_v3_robust; print('✓ Benchmark script OK')"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error("Failed to import benchmark script!")
            logger.error(result.stderr)
            sys.exit(1)
        logger.info(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to verify benchmark script: {e}")
        sys.exit(1)
    
    # Validate environment
    available_providers = validate_environment()
    
    # Count total models
    total_models = sum(
        len(models) for provider, models in MODEL_CONFIGS.items()
        if available_providers.get(provider, False)
    )
    
    logger.info(f"\nTotal models to test: {total_models}")
    logger.info("Starting benchmark run...\n")
    
    # Track results
    results = {
        'attempted': {provider: [] for provider in MODEL_CONFIGS.keys()},
        'start_time': datetime.now(),
    }
    
    # Run benchmarks
    model_counter = 0
    for provider, models in MODEL_CONFIGS.items():
        if not available_providers.get(provider, False):
            logger.warning(f"\nSkipping {provider} models (no API key)")
            continue
        
        logger.info(f"\n{'='*70}")
        logger.info(f"TESTING {provider.upper()} MODELS ({len(models)} models)")
        logger.info(f"{'='*70}")
        
        for config in models:
            model_counter += 1
            model_name = config.get("label", f"{provider}/{config['model']}")
            
            logger.info(f"\n[{model_counter}/{total_models}] {model_name}")
            
            # Run with streaming output
            success, error = run_single_benchmark_streaming(provider, config)
            
            results['attempted'][provider].append({
                'model': config['model'],
                'label': model_name,
                'success': success,
                'error': error,
                'enhanced_prompt': config.get('enhanced_prompt', False)
            })
            
            # Brief pause between models
            if model_counter < total_models:
                logger.info("Pausing 5 seconds before next model...")
                time.sleep(5)
    
    # Generate summary
    results['end_time'] = datetime.now()
    results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
    
    # Summary report
    logger.info("\n" + "="*70)
    logger.info("BENCHMARK COMPLETE")
    logger.info("="*70)
    
    total_attempted = sum(len(m) for m in results['attempted'].values())
    total_success = sum(
        len([m for m in models if m['success']]) 
        for models in results['attempted'].values()
    )
    
    logger.info(f"Duration: {results['duration']/3600:.1f} hours")
    logger.info(f"Total attempted: {total_attempted}")
    logger.info(f"Successful: {total_success}")
    logger.info(f"Failed: {total_attempted - total_success}")
    
    # Save summary
    summary_file = log_dir / f"benchmark_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nSummary saved to: {summary_file}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Results: results_v3/")
    
    # Try to generate dashboard
    if total_success > 0:
        logger.info("\nGenerating dashboard...")
        try:
            result = subprocess.run(
                ["poetry", "run", "python", "generate_v3_dashboard_comprehensive.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info("✓ Dashboard generated successfully")
            else:
                logger.warning("Dashboard generation failed")
        except:
            logger.warning("Dashboard generation failed")
    
    logger.info("\n✨ Overnight benchmark complete!")

if __name__ == "__main__":
    main()