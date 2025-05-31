#!/usr/bin/env python3
"""
SchizoBench Model Comparison Script

This script runs the SchizoBench v3 multi-turn analysis on all specified frontier models,
saving results for each model in a standardized format.
"""

import os
import subprocess
import time
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define models to test
ANTHROPIC_MODELS = [
    "claude-opus-4-20250514",
    "claude-sonnet-4-20250514",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229"
]

OPENAI_MODELS = [
    "gpt-4.1-2025-04-14",
    "o4-mini-2025-04-16",
    "gpt-4o-2024-08-06"
]

# Function to run benchmark for a model
def run_benchmark(provider, model, scoring_provider="openai", scoring_model="gpt-4.1-2025-04-14", 
                 system_prompt=None, temperature=0.7):
    """Run benchmark for a specific model"""
    
    # Special handling for o4-mini (it only works with temperature=1)
    if model == "o4-mini-2025-04-16":
        temperature = 1.0
    
    model_str = model.replace(".", "-")  # Replace dots for filename compatibility
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Build command with poetry
    cmd = [
        "poetry", "run", "python", "run_benchmark_v3_improved.py",
        "--provider", provider,
        "--model", model,
        "--temperature", str(temperature),
        "--scoring-provider", scoring_provider,
        "--scoring-model", scoring_model
    ]
    
    # Add system prompt if specified
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    
    # Construct a descriptive output prefix
    run_description = f"{provider}_{model_str}"
    if system_prompt:
        run_description += "_custom_prompt"
    run_description += f"_{timestamp}"
    
    # Log file
    log_dir = "benchmark_logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{run_description}.log")
    
    logger.info(f"Starting benchmark for {provider}/{model}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info(f"Log file: {log_file}")
    
    # Run the command
    with open(log_file, "w") as f:
        f.write(f"SchizoBench v3 run for {provider}/{model}\n")
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n\n")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Stream output to log file
            for line in process.stdout:
                f.write(line)
                f.flush()  # Ensure it's written immediately
            
            process.wait()
            
            f.write(f"\nCompleted: {datetime.now().isoformat()}\n")
            f.write(f"Exit code: {process.returncode}\n")
            
            # Check for generated results files to determine partial success
            result_files = []
            for file in os.listdir("results_v3"):
                if file.startswith(f"schizobench_v3_{model_str}") and file.endswith(".json"):
                    result_files.append(os.path.join("results_v3", file))
            
            if result_files:
                # Check if any result file has non-zero size and valid content
                valid_results = False
                for file_path in result_files:
                    if os.path.getsize(file_path) > 1000:  # Non-trivial file size
                        try:
                            with open(file_path, 'r') as json_file:
                                data = json.load(json_file)
                                if 'results' in data and len(data['results']) > 0:
                                    valid_results = True
                                    break
                        except json.JSONDecodeError:
                            pass
                
                if valid_results:
                    if process.returncode == 0:
                        logger.info(f"✅ Benchmark completed successfully for {provider}/{model}")
                        return True
                    else:
                        logger.warning(f"⚠️ Benchmark partially completed for {provider}/{model} - found valid results despite exit code {process.returncode}")
                        return "partial"
                else:
                    logger.error(f"❌ Benchmark failed for {provider}/{model} with exit code {process.returncode} - found results files but no valid data")
                    return False
            else:
                logger.error(f"❌ Benchmark failed for {provider}/{model} with exit code {process.returncode} - no results files found")
                return False
                
        except Exception as e:
            error_msg = f"Error running benchmark: {str(e)}"
            f.write(f"\n{error_msg}\n")
            logger.error(error_msg)
            return False

def main():
    """Run benchmarks for all models"""
    logger.info("=" * 80)
    logger.info("SchizoBench Model Comparison")
    logger.info("=" * 80)
    
    results_dir = "results_comparison"
    os.makedirs(results_dir, exist_ok=True)
    
    # Create summary file
    summary_file = os.path.join(results_dir, f"benchmark_summary_{datetime.now().strftime('%Y%m%d')}.txt")
    with open(summary_file, "w") as f:
        f.write("SchizoBench v3 Model Comparison\n")
        f.write(f"Started: {datetime.now().isoformat()}\n\n")
        f.write("Model,Status,Timestamp\n")
    
    # 1. Run all Anthropic models with default system prompt
    logger.info("\nRunning Anthropic models with default system prompt:")
    for model in ANTHROPIC_MODELS:
        result = run_benchmark("anthropic", model)
        
        # Determine status text based on result
        if result == True:
            status = "Success"
        elif result == "partial":
            status = "Partial"
        else:
            status = "Failed"
            
        with open(summary_file, "a") as f:
            f.write(f"anthropic/{model},{status},{datetime.now().isoformat()}\n")
        
        # Small delay between runs
        time.sleep(5)
    
    # 2. Run Claude Opus 4 with enhanced system prompt
    logger.info("\nRunning Claude Opus 4 with enhanced system prompt:")
    enhanced_prompt_path = os.path.join("archive", "claude_system_prompt_enhanced.txt")
    if not os.path.exists(enhanced_prompt_path):
        logger.error(f"Enhanced prompt file not found at {enhanced_prompt_path}")
        enhanced_prompt = None
    else:
        with open(enhanced_prompt_path, "r") as f:
            enhanced_prompt = f.read().strip()
    
    if enhanced_prompt:
        result = run_benchmark("anthropic", "claude-opus-4-20250514", system_prompt=enhanced_prompt)
    else:
        logger.warning("Skipping enhanced prompt test for Claude Opus 4")
        result = False
    
    # Determine status text based on result
    if result == True:
        status = "Success"
    elif result == "partial":
        status = "Partial"
    else:
        status = "Failed"
        
    with open(summary_file, "a") as f:
        f.write(f"anthropic/claude-opus-4-20250514-enhanced,{status},{datetime.now().isoformat()}\n")
    
    time.sleep(5)
    
    # 3. Run OpenAI models
    logger.info("\nRunning OpenAI models:")
    for model in OPENAI_MODELS:
        result = run_benchmark("openai", model)
        
        # Determine status text based on result
        if result == True:
            status = "Success"
        elif result == "partial":
            status = "Partial"
        else:
            status = "Failed"
            
        with open(summary_file, "a") as f:
            f.write(f"openai/{model},{status},{datetime.now().isoformat()}\n")
        
        time.sleep(5)
    
    # Update summary with completion
    with open(summary_file, "a") as f:
        f.write(f"\nCompleted: {datetime.now().isoformat()}\n")
    
    logger.info("\nAll benchmarks completed. Results saved to results_v3/ directory.")
    logger.info(f"Summary file: {summary_file}")
    
    # Generate metrics dashboard
    try:
        logger.info("\nGenerating metrics dashboard...")
        
        # Check if there are any valid result files to process
        has_valid_results = False
        for filename in os.listdir("results_v3"):
            if filename.endswith(".json") and os.path.getsize(os.path.join("results_v3", filename)) > 1000:
                try:
                    with open(os.path.join("results_v3", filename), 'r') as f:
                        data = json.load(f)
                        if 'results' in data and len(data['results']) > 0:
                            has_valid_results = True
                            break
                except:
                    pass
        
        if not has_valid_results:
            logger.warning("⚠️ No valid result files found for dashboard generation. Dashboard may be incomplete.")
            
        # Try comparison dashboard first (if we have enhanced prompt results)
        dashboard_cmd = ["poetry", "run", "python", "generate_v3_dashboard_comparison.py"]
        dashboard_process = subprocess.run(dashboard_cmd, check=False, capture_output=True, text=True, timeout=120)
        
        if dashboard_process.returncode == 0:
            logger.info("✅ Comparison dashboard generated successfully")
            logger.info("Check: results_v3/visualizations/schizobench_v3_dashboard_comparison.html")
        else:
            logger.info("Comparison dashboard not available, trying standard dashboard...")
            # Fall back to standard dashboard
            dashboard_cmd = ["poetry", "run", "python", "generate_v3_dashboard_dark.py"]
            dashboard_process = subprocess.run(dashboard_cmd, check=False, capture_output=True, text=True, timeout=120)
            
            if dashboard_process.returncode == 0:
                logger.info("✅ Standard dashboard generated successfully")
                # Extract dashboard location from output
                for line in dashboard_process.stdout.split('\n'):
                    if "Location:" in line:
                        logger.info(line.strip())
            else:
                logger.error(f"❌ Dashboard generation failed with exit code {dashboard_process.returncode}")
                logger.error(f"Error details: {dashboard_process.stderr}")
            
            # Try to create a minimal dashboard with just the summary information
            logger.info("Attempting to create a minimal dashboard with summary information...")
            with open(os.path.join(results_dir, "minimal_dashboard.html"), "w") as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>SchizoBench Minimal Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>SchizoBench Minimal Dashboard</h1>
    <p>This is a minimal dashboard generated because the full dashboard generation failed.</p>
    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Run Summary</h2>
    <table>
        <tr>
            <th>Model</th>
            <th>Status</th>
            <th>Timestamp</th>
        </tr>
""")
                
                # Add data from summary file
                with open(summary_file, "r") as summary:
                    lines = summary.readlines()
                    for line in lines[3:]:  # Skip header lines
                        if line.strip() and "," in line:
                            model, status, timestamp = line.strip().split(",", 2)
                            f.write(f"        <tr>\n")
                            f.write(f"            <td>{model}</td>\n")
                            f.write(f"            <td>{status}</td>\n")
                            f.write(f"            <td>{timestamp}</td>\n")
                            f.write(f"        </tr>\n")
                
                f.write("""
    </table>
    
    <p>For full results, please check the individual result files in the results_v3 directory.</p>
</body>
</html>
""")
                logger.info(f"Minimal dashboard created at: {os.path.join(results_dir, 'minimal_dashboard.html')}")
    
    except Exception as e:
        logger.error(f"❌ Error generating dashboard: {str(e)}")
        logger.info("Check individual result files in results_v3/ for available data.")

if __name__ == "__main__":
    main()