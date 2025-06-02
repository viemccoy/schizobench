#!/usr/bin/env python3
"""
Final Benchmark Starter with Live Progress Display
"""

import os
import sys
import subprocess
import time
import threading
from datetime import datetime

# Ensure we're using the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print a nice banner"""
    print("\n" + "="*80)
    print("🚀 SCHIZOBENCH v3.0 - FINAL BENCHMARK RUN 🚀".center(80))
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing 38 models with 44 sequences each")
    print(f"Using GPT-4.1 for reification scoring")
    print("="*80 + "\n")

def monitor_progress():
    """Monitor the benchmark progress"""
    log_file = None
    
    # Find the latest log file
    for i in range(10):
        files = [f for f in os.listdir('.') if f.startswith('overnight_') and f.endswith('.log')]
        if files:
            log_file = max(files, key=os.path.getctime)
            break
        time.sleep(1)
    
    if not log_file:
        print("⚠️  No log file found yet...")
        return
        
    print(f"📄 Monitoring log: {log_file}\n")
    
    # Track progress
    last_size = 0
    no_change_count = 0
    
    while True:
        try:
            size = os.path.getsize(log_file)
            
            if size > last_size:
                # File is growing, benchmark is running
                with open(log_file, 'r') as f:
                    f.seek(last_size)
                    new_content = f.read()
                    
                    # Parse for interesting updates
                    for line in new_content.split('\n'):
                        if "--- Model" in line:
                            print(f"\n🤖 {line.strip()}")
                        elif "Starting benchmark for" in line:
                            model = line.split("for ")[-1].split(" (")[0]
                            print(f"   ▶️  Testing: {model}")
                        elif "Successfully completed" in line:
                            print(f"   ✅ {line.strip()}")
                        elif "Failed" in line and "✗" in line:
                            print(f"   ❌ {line.strip()}")
                        elif "Timeout" in line:
                            print(f"   ⏱️  {line.strip()}")
                            
                last_size = size
                no_change_count = 0
            else:
                no_change_count += 1
                if no_change_count % 60 == 0:  # Every minute of no activity
                    print(f"   ⏳ Still running... (no activity for {no_change_count} seconds)")
                    
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped. Benchmark continues in background.")
            break
        except Exception as e:
            print(f"\n⚠️  Monitor error: {e}")
            break

def main():
    """Start the benchmark with monitoring"""
    print_banner()
    
    # Check environment
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Checking API keys...")
    api_keys = {
        "ANTHROPIC": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI": os.getenv("OPENAI_API_KEY"), 
        "GOOGLE": os.getenv("GOOGLE_API_KEY"),
        "OPENROUTER": os.getenv("OPENROUTER_API_KEY")
    }
    
    missing = [k for k, v in api_keys.items() if not v]
    if missing:
        print(f"❌ ERROR: Missing API keys: {missing}")
        print("Please ensure all API keys are in .env file")
        return 1
        
    print("✅ All API keys loaded\n")
    
    # Clean up old results
    print("Cleaning up old results...")
    os.system("rm -f results_v3/*.json results_v3/*.csv results_v3/*.txt 2>/dev/null")
    print("✅ Results directory cleaned\n")
    
    # Start benchmark
    print("Starting benchmark...")
    log_file = f"overnight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    cmd = ["poetry", "run", "python", "run_overnight.py"]
    process = subprocess.Popen(
        cmd,
        stdout=open(log_file, 'w'),
        stderr=subprocess.STDOUT,
        bufsize=1
    )
    
    print(f"✅ Benchmark started (PID: {process.pid})")
    print(f"📄 Log file: {log_file}")
    print("\nMonitoring progress (press Ctrl+C to stop monitoring)...")
    print("-" * 80)
    
    # Start monitoring in main thread
    try:
        monitor_progress()
    except KeyboardInterrupt:
        pass
    
    print("\n" + "-" * 80)
    print("Benchmark is running in the background.")
    print(f"To check status: tail -f {log_file}")
    print(f"To stop benchmark: kill {process.pid}")
    print("\nExpected duration: 3-5 hours")
    print("\n💙 Good luck! The models are being tested for safety! 💙")

if __name__ == "__main__":
    main()