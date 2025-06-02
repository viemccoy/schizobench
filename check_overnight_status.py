#!/usr/bin/env python3
"""Quick status check for overnight benchmark run"""

import os
import json
from datetime import datetime
from pathlib import Path

def check_status():
    # Check log files
    log_dir = Path("benchmark_logs")
    latest_log = None
    
    if log_dir.exists():
        logs = sorted(log_dir.glob("overnight_run_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if logs:
            latest_log = logs[0]
            print(f"📄 Latest log: {latest_log}")
            
            # Get last few lines
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                print(f"\n📊 Last 5 log entries:")
                for line in lines[-5:]:
                    print(f"  {line.strip()}")
    
    # Check results
    results_dir = Path("results_v3")
    if results_dir.exists():
        json_files = list(results_dir.glob("*.json"))
        print(f"\n📁 Total result files: {len(json_files)}")
        
        # Get recent results
        recent = sorted(json_files, key=lambda p: p.stat().st_mtime, reverse=True)[:3]
        if recent:
            print("\n🕒 Most recent results:")
            for f in recent:
                timestamp = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M:%S")
                print(f"  {timestamp} - {f.name}")
    
    # Check if processes are running
    print("\n🏃 Running processes:")
    os.system("ps aux | grep -E '(run_overnight|monitor_live)' | grep -v grep | awk '{print $11, $12, $13}'")

if __name__ == "__main__":
    print("SchizoBench Overnight Status Check")
    print("="*50)
    check_status()