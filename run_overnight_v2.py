#!/usr/bin/env python3
"""
Enhanced overnight benchmark runner with ModelFactory integration and live progress
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Setup logging
log_dir = Path("benchmark_logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"overnight_run_{timestamp}.log"

# Configure logging to both file and console with colors
class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

# File handler (no colors)
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Console handler (with colors)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# Model configurations organized by provider
MODEL_CONFIGS = {
    "anthropic": [
        # Claude 4 family
        {"model": "claude-opus-4-20250514", "slow": True},
        {"model": "claude-sonnet-4-20250514", "slow": True},
        
        # Claude 3.7
        {"model": "claude-3-7-sonnet-20250219", "slow": True},
        
        # Claude 3.5 family
        {"model": "claude-3-5-sonnet-20241022"},   # Sonnet 3.5 v2
        {"model": "claude-3-5-sonnet-20240620"},   # Sonnet 3.5 v1
        {"model": "claude-3-5-haiku-20241022"},    # Haiku 3.5
        
        # Claude 3 family
        {"model": "claude-3-opus-20240229", "slow": True},
        {"model": "claude-3-haiku-20240307"},      # Haiku 3
        
        # Special test with enhanced prompt
        {"model": "claude-opus-4-20250514", "slow": True, "enhanced_prompt": True, "label": "Claude Opus 4 (Enhanced)"},
    ],
    
    "openai": [
        # GPT-4.1 family
        {"model": "gpt-4.1-2025-04-14"},
        {"model": "gpt-4.1-mini-2025-04-14"},
        {"model": "gpt-4.1-nano-2025-04-14"},
        
        # GPT-4o family
        {"model": "gpt-4o-2024-08-06"},
        {"model": "gpt-4o-mini-2024-07-18"},
        
        # O-series models (reasoning models)
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
        # DeepSeek models
        {"model": "deepseek/deepseek-r1-0528:free"},
        {"model": "deepseek/deepseek-chat-v3-0324:free"},
        {"model": "deepseek/deepseek-r1:free"},
        {"model": "deepseek/deepseek-chat:free"},
        
        # X.AI Grok models
        {"model": "x-ai/grok-3-beta"},
        {"model": "x-ai/grok-3-mini-beta"},
        {"model": "x-ai/grok-2-1212"},
        
        # Meta Llama models
        {"model": "meta-llama/llama-4-maverick:free"},
        {"model": "meta-llama/llama-4-scout:free"},
        {"model": "meta-llama/llama-3.3-70b-instruct:free"},
        {"model": "meta-llama/llama-3.1-405b-instruct", "slow": True},
        {"model": "meta-llama/llama-3.1-70b-instruct"},
        {"model": "meta-llama/llama-3-70b-instruct"},
        
        # NousResearch Hermes models
        {"model": "nousresearch/hermes-3-llama-3.1-70b"},
        {"model": "nousresearch/hermes-3-llama-3.1-405b", "slow": True},
    ]
}

def validate_environment() -> Dict[str, bool]:
    """Validate API keys are available"""
    providers = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    
    available = {}
    for provider, env_var in providers.items():
        if os.getenv(env_var):
            available[provider] = True
            logger.info(f"✓ {provider.capitalize()} API key found")
        else:
            available[provider] = False
            logger.warning(f"✗ {env_var} not set - {provider} models will be skipped")
    
    return available

def get_timeout_for_model(config: Dict) -> int:
    """Determine appropriate timeout based on model characteristics"""
    if config.get("slow", False):
        return 14400  # 4 hours for slow models
    return 7200  # 2 hours default

def run_single_benchmark(provider: str, config: Dict, retry_count: int = 0, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """Run benchmark for a single model with retry logic"""
    
    model = config["model"]
    temperature = config.get("temperature", 0.7)
    enhanced_prompt = config.get("enhanced_prompt", False)
    label = config.get("label", f"{provider}/{model}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting: {label}")
    logger.info(f"Attempt: {retry_count + 1}/{max_retries}")
    
    if enhanced_prompt:
        logger.info("Using enhanced system prompt")
    
    timeout_seconds = get_timeout_for_model(config)
    logger.info(f"Timeout: {timeout_seconds/3600:.1f} hours")
    
    try:
        # Build command
        cmd = [
            "poetry", "run", "python", "run_benchmark_v3_improved.py",
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
                logger.error(f"Enhanced prompt file not found at {enhanced_prompt_path}")
                return False, "Enhanced prompt file missing"
        
        # Run the benchmark
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✓ Successfully completed {label} in {elapsed_time/60:.1f} minutes")
            return True, None
        else:
            error_msg = f"Exit code {result.returncode}: {result.stderr[:500]}"
            logger.warning(f"✗ Failed {label} - {error_msg}")
            
            # Check if partial results were generated
            if check_partial_results(model):
                logger.info(f"⚠ Partial results found for {label}")
                return True, "Partial results"
            
            if retry_count < max_retries - 1:
                wait_time = 30 * (retry_count + 1)  # Exponential backoff
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                return run_single_benchmark(provider, config, retry_count + 1, max_retries)
            
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = f"Timeout after {timeout_seconds/3600:.1f} hours"
        logger.error(f"✗ {error_msg} for {label}")
        
        # Check if partial results exist
        if check_partial_results(model):
            logger.info(f"⚠ Partial results found despite timeout for {label}")
            return True, "Timeout with partial results"
            
        return False, error_msg
        
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
            if file.stat().st_size > 1000:  # Non-trivial size
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        # Check if it has actual sequence results
                        if isinstance(data, dict):
                            if "sequences" in data and len(data.get("sequences", [])) > 0:
                                return True
                            elif "turns" in data and len(data.get("turns", [])) > 0:
                                return True
                except:
                    pass
    return False

def generate_summary_report(results: Dict[str, List[Dict]]) -> None:
    """Generate a summary report of the benchmark run"""
    
    total_models = sum(len(models) for models in results['attempted'].values())
    total_successful = sum(len([m for m in models if m['success']]) for models in results['attempted'].values())
    total_failed = total_models - total_successful
    
    logger.info("\n" + "="*70)
    logger.info("BENCHMARK SUMMARY")
    logger.info("="*70)
    logger.info(f"Total models attempted: {total_models}")
    logger.info(f"Successful: {total_successful}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Success rate: {total_successful/total_models*100:.1f}%")
    
    # Per-provider breakdown
    logger.info("\nPer-Provider Breakdown:")
    for provider, models in results['attempted'].items():
        if models:
            successful = len([m for m in models if m['success']])
            logger.info(f"\n{provider.upper()}:")
            logger.info(f"  Attempted: {len(models)}")
            logger.info(f"  Successful: {successful}")
            logger.info(f"  Failed: {len(models) - successful}")
            
            # List failed models
            failed_models = [m for m in models if not m['success']]
            if failed_models:
                logger.info(f"  Failed models:")
                for m in failed_models:
                    logger.info(f"    ✗ {m['model']} - {m.get('error', 'Unknown error')}")

def main():
    """Main overnight benchmark runner"""
    logger.info("="*70)
    logger.info("SchizoBench v3.0 Overnight Benchmark")
    logger.info("Enhanced with ModelFactory and Live Progress")
    logger.info("="*70)
    
    # Validate environment
    available_providers = validate_environment()
    
    # Initialize results tracking
    results = {
        'attempted': {provider: [] for provider in MODEL_CONFIGS.keys()},
        'start_time': datetime.now(),
    }
    
    # Count total models to run
    total_models = 0
    for provider, models in MODEL_CONFIGS.items():
        if available_providers.get(provider, False):
            total_models += len(models)
    
    logger.info(f"\nTotal models to test: {total_models}")
    
    # Run benchmarks
    model_counter = 0
    for provider, models in MODEL_CONFIGS.items():
        if not available_providers.get(provider, False):
            logger.warning(f"\nSkipping {provider} models (no API key)")
            continue
            
        logger.info(f"\n{'='*70}")
        logger.info(f"TESTING {provider.upper()} MODELS")
        logger.info(f"{'='*70}")
        
        for config in models:
            model_counter += 1
            model_name = config.get("label", f"{provider}/{config['model']}")
            
            logger.info(f"\n[{model_counter}/{total_models}] {model_name}")
            
            success, error = run_single_benchmark(provider, config)
            
            results['attempted'][provider].append({
                'model': config['model'],
                'label': model_name,
                'success': success,
                'error': error,
                'enhanced_prompt': config.get('enhanced_prompt', False)
            })
            
            # Brief pause between models
            if model_counter < total_models:
                time.sleep(5)
    
    # Generate summary
    results['end_time'] = datetime.now()
    results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
    
    generate_summary_report(results)
    
    # Save results summary
    summary_file = log_dir / f"benchmark_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"\nResults summary saved to: {summary_file}")
    
    # Generate dashboard if we have results
    successful_count = sum(
        len([m for m in models if m['success']]) 
        for models in results['attempted'].values()
    )
    
    if successful_count > 0:
        logger.info("\nGenerating dashboard...")
        try:
            result = subprocess.run(
                ["poetry", "run", "python", "generate_v3_dashboard_comprehensive.py"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✓ Dashboard generated successfully")
                logger.info("Check: results_v3/visualizations/schizobench_v3_dashboard_comprehensive.html")
            else:
                logger.warning("✗ Dashboard generation failed")
                logger.warning(f"Error: {result.stderr[:200]}")
        except Exception as e:
            logger.warning(f"✗ Dashboard generation failed: {e}")
    
    # Final summary
    logger.info(f"\n{'='*70}")
    logger.info("BENCHMARK COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"Duration: {results['duration']/3600:.1f} hours")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Results: results_v3/")
    logger.info("\n🎉 Overnight benchmark run complete!")

if __name__ == "__main__":
    main()