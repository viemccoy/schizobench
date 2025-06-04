#!/usr/bin/env python3
"""
Real-time benchmark progress monitor with ETA estimation
Shows beautiful progress bars and statistics
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple, Optional
import sys
import os

# ANSI color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def get_completed_models() -> List[str]:
    """Get list of completed models from results directory"""
    results_dir = Path("results_v3")
    completed = []
    
    for json_file in results_dir.glob("*.json"):
        if 'transcripts' not in str(json_file):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    model = data['metadata']['model']
                    provider = data['metadata']['provider']
                    completed.append(f"{provider}/{model}")
            except:
                pass
    
    return completed

def get_current_model_progress() -> Tuple[Optional[str], Optional[int], int]:
    """Get current model and sequence progress"""
    try:
        # Check running process
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        # Find benchmark process
        for line in result.stdout.split('\n'):
            if 'run_benchmark_v3_robust.py' in line and 'grep' not in line:
                # Extract provider and model from command line
                match_provider = re.search(r'--provider\s+(\S+)', line)
                match_model = re.search(r'--model\s+(\S+)', line)
                
                if match_provider and match_model:
                    provider = match_provider.group(1)
                    model = match_model.group(1)
                    current_model = f"{provider}/{model}"
                    
                    # Get sequence progress from log
                    log_tail = subprocess.run(
                        ["tail", "-100", "overnight_run_v3.log"],
                        capture_output=True,
                        text=True
                    )
                    
                    # Find most recent progress
                    progress_matches = re.findall(r'PROGRESS:\s*(\d+)/(\d+)', log_tail.stdout)
                    if progress_matches:
                        current, total = progress_matches[-1]
                        return current_model, int(current), int(total)
                    
                    return current_model, 0, 44
        
        return None, None, 44
    except:
        return None, None, 44

def get_model_start_times() -> Dict[str, datetime]:
    """Parse log to get start times for timing estimation"""
    start_times = {}
    
    try:
        with open("overnight_run_v3.log", 'r') as f:
            for line in f:
                if "Starting:" in line and "===" not in line:
                    # Extract timestamp and model
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Starting:\s+(.+)', line)
                    if match:
                        timestamp_str = match.group(1)
                        model = match.group(2).strip()
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        start_times[model] = timestamp
    except:
        pass
    
    return start_times

def calculate_eta(completed_count: int, total_count: int, start_times: Dict[str, datetime]) -> Optional[str]:
    """Calculate estimated time of completion"""
    if completed_count == 0:
        return None
    
    # Get average time per model from completed ones
    completed_times = []
    for model, start_time in start_times.items():
        # Check if this model has results
        results_exist = any(Path("results_v3").glob(f"*{model.split('/')[-1]}*.json"))
        if results_exist:
            # Find end time (approximate from next model start or now)
            end_time = None
            sorted_times = sorted([(m, t) for m, t in start_times.items()], key=lambda x: x[1])
            for i, (m, t) in enumerate(sorted_times):
                if m == model and i < len(sorted_times) - 1:
                    end_time = sorted_times[i + 1][1]
                    break
            
            if end_time:
                duration = (end_time - start_time).total_seconds() / 3600  # hours
                completed_times.append(duration)
    
    if not completed_times:
        # Fallback: estimate based on total elapsed time
        first_start = min(start_times.values()) if start_times else datetime.now()
        total_elapsed = (datetime.now() - first_start).total_seconds() / 3600
        avg_time_per_model = total_elapsed / max(completed_count, 1)
    else:
        avg_time_per_model = sum(completed_times) / len(completed_times)
    
    remaining_models = total_count - completed_count
    estimated_hours = remaining_models * avg_time_per_model
    eta = datetime.now() + timedelta(hours=estimated_hours)
    
    return eta.strftime('%Y-%m-%d %H:%M')

def draw_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Draw a nice progress bar"""
    percent = current / total
    filled = int(width * percent)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percent*100:.1f}%"

def format_duration(hours: float) -> str:
    """Format duration in human-readable format"""
    if hours < 1:
        return f"{int(hours * 60)} minutes"
    elif hours < 24:
        return f"{hours:.1f} hours"
    else:
        days = int(hours / 24)
        remaining_hours = hours % 24
        return f"{days} days, {int(remaining_hours)} hours"

def monitor_progress(refresh_interval: int = 30):
    """Main monitoring loop"""
    
    # All expected models
    all_models = [
        # Anthropic (9)
        "anthropic/claude-opus-4-20250514",
        "anthropic/claude-sonnet-4-20250514",
        "anthropic/claude-3-7-sonnet-20250219",
        "anthropic/claude-3-5-sonnet-20241022",
        "anthropic/claude-3-5-sonnet-20240620",
        "anthropic/claude-3-5-haiku-20241022",
        "anthropic/claude-3-opus-20240229",
        "anthropic/claude-3-haiku-20240307",
        "anthropic/claude-opus-4-20250514 (Enhanced)",
        # OpenAI (10)
        "openai/gpt-4.1-2025-04-14",
        "openai/gpt-4.1-mini-2025-04-14",
        "openai/gpt-4.1-nano-2025-04-14",
        "openai/gpt-4o-2024-08-06",
        "openai/gpt-4o-mini-2024-07-18",
        "openai/o3-2025-04-16",
        "openai/o3-mini-2025-01-31",
        "openai/o4-mini-2025-04-16",
        "openai/o1-2024-12-17",
        "openai/o1-mini-2024-09-12",
        # Google (4)
        "google/gemini-2.5-pro-preview-05-06",
        "google/gemini-2.5-flash-preview-05-20",
        "google/gemini-2.0-flash-exp",
        "google/gemini-2.0-flash-lite",
        # OpenRouter (15)
        "openrouter/deepseek/deepseek-r1-0528:free",
        "openrouter/deepseek/deepseek-chat-v3-0324:free",
        "openrouter/deepseek/deepseek-r1:free",
        "openrouter/deepseek/deepseek-chat:free",
        "openrouter/x-ai/grok-3-beta",
        "openrouter/x-ai/grok-3-mini-beta",
        "openrouter/x-ai/grok-2-1212",
        "openrouter/meta-llama/llama-4-maverick:free",
        "openrouter/meta-llama/llama-4-scout:free",
        "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        "openrouter/meta-llama/llama-3.1-405b-instruct",
        "openrouter/meta-llama/llama-3.1-70b-instruct",
        "openrouter/meta-llama/llama-3-70b-instruct",
        "openrouter/nousresearch/hermes-3-llama-3.1-70b",
        "openrouter/nousresearch/hermes-3-llama-3.1-405b",
    ]
    
    while True:
        clear_screen()
        
        # Header
        print(f"{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}║         SchizoBench v3.0 - Live Progress Monitor             ║{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        print()
        
        # Get current state
        completed = get_completed_models()
        current_model, current_seq, total_seq = get_current_model_progress()
        start_times = get_model_start_times()
        
        # Overall progress
        total_models = len(all_models)
        completed_count = len(completed)
        
        print(f"{Colors.CYAN}{Colors.BOLD}Overall Progress:{Colors.ENDC}")
        print(f"Models: {completed_count}/{total_models} " + draw_progress_bar(completed_count, total_models))
        print()
        
        # Current model progress
        if current_model and current_seq is not None:
            print(f"{Colors.YELLOW}{Colors.BOLD}Currently Running:{Colors.ENDC}")
            print(f"Model: {current_model}")
            print(f"Sequence: {current_seq}/{total_seq} " + draw_progress_bar(current_seq, total_seq, 30))
            
            # Time estimate for current model
            if current_model in start_times:
                elapsed = (datetime.now() - start_times[current_model]).total_seconds() / 3600
                if current_seq > 0:
                    est_total = (elapsed / current_seq) * total_seq
                    remaining = est_total - elapsed
                    print(f"Time elapsed: {format_duration(elapsed)} | ETA: {format_duration(remaining)}")
            print()
        
        # Completed models by provider
        print(f"{Colors.GREEN}{Colors.BOLD}Completed Models:{Colors.ENDC}")
        providers = {}
        for model in completed:
            provider = model.split('/')[0]
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model)
        
        for provider, models in sorted(providers.items()):
            print(f"  {provider}: {len(models)} models ✓")
        print()
        
        # Failed/Timeout models
        print(f"{Colors.FAIL}{Colors.BOLD}Known Issues:{Colors.ENDC}")
        if "openai/gpt-4.1-2025-04-14" not in completed:
            print(f"  • GPT-4.1: Timed out (retry pending with 6h timeout)")
        print()
        
        # ETA calculation
        eta = calculate_eta(completed_count, total_models, start_times)
        if eta:
            print(f"{Colors.BLUE}{Colors.BOLD}Estimated Completion:{Colors.ENDC} {eta}")
            
            # Average time per model
            if completed_count > 0:
                first_start = min(start_times.values()) if start_times else datetime.now()
                total_elapsed = (datetime.now() - first_start).total_seconds() / 3600
                avg_time = total_elapsed / completed_count
                print(f"Average time per model: {format_duration(avg_time)}")
        
        # Footer
        print()
        print(f"{Colors.CYAN}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print(f"Refreshing every {refresh_interval} seconds... (Ctrl+C to exit)")
        
        # Special messages
        if completed_count == total_models:
            print()
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL MODELS COMPLETE! Time to generate that beautiful dashboard! 🎉{Colors.ENDC}")
            break
        
        try:
            time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Monitoring stopped. Benchmark continues in background.{Colors.ENDC}")
            break

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor SchizoBench progress")
    parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds")
    args = parser.parse_args()
    
    monitor_progress(args.interval)