#!/usr/bin/env python3
"""
Live Benchmark Dashboard - Shows real-time progress and model responses
"""

import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime
from collections import deque
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('live_dashboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LiveBenchmarkDashboard:
    def __init__(self):
        self.current_model = None
        self.current_sequence = None
        self.current_turn = 0
        self.responses = deque(maxlen=10)  # Keep last 10 responses
        self.start_time = datetime.now()
        self.models_completed = 0
        self.models_failed = 0
        self.total_sequences = 0
        self.sequences_completed = 0
        self.reifications_detected = 0
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def format_time_elapsed(self):
        elapsed = datetime.now() - self.start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        seconds = int(elapsed.total_seconds() % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    def display(self):
        self.clear_screen()
        print("=" * 80)
        print("🚀 SCHIZOBENCH v3.0 - LIVE BENCHMARK DASHBOARD 🚀".center(80))
        print("=" * 80)
        
        # Overall stats
        print(f"\n⏱️  Time Elapsed: {self.format_time_elapsed()}")
        print(f"📊 Models: {self.models_completed} completed, {self.models_failed} failed")
        print(f"🔄 Sequences: {self.sequences_completed}/{self.total_sequences}")
        print(f"⚠️  Reifications Detected: {self.reifications_detected}")
        
        # Current activity
        print("\n" + "-" * 80)
        print("CURRENT ACTIVITY:")
        if self.current_model:
            print(f"🤖 Model: {self.current_model}")
            print(f"📝 Sequence: {self.current_sequence or 'Starting...'}")
            print(f"💬 Turn: {self.current_turn}")
        else:
            print("⏳ Waiting to start...")
            
        # Recent responses
        print("\n" + "-" * 80)
        print("RECENT RESPONSES:")
        if self.responses:
            for resp in self.responses:
                print(f"\n[{resp['time']}] {resp['model']} - Turn {resp['turn']}")
                print(f"👤 User: {resp['user_msg'][:100]}...")
                print(f"🤖 Model: {resp['model_response'][:150]}...")
                if resp.get('reification'):
                    print(f"⚠️  REIFICATION: {resp['reification']}")
        else:
            print("No responses yet...")
            
        print("\n" + "=" * 80)
        print("Press Ctrl+C to stop monitoring (benchmark will continue)")
        
    def update_from_log(self, line):
        """Parse log line and update dashboard state"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Parse different log patterns
        if "Testing model:" in line:
            self.current_model = line.split("Testing model: ")[-1].strip()
            self.current_sequence = None
            self.current_turn = 0
            
        elif "Evaluating sequence:" in line:
            self.current_sequence = line.split("Evaluating sequence: ")[-1].strip()
            self.current_turn = 0
            
        elif "Turn " in line and "User:" in line:
            try:
                self.current_turn = int(line.split("Turn ")[1].split()[0])
                user_msg = line.split("User: ")[-1].strip()
                # Store for pairing with response
                self.last_user_msg = user_msg
            except:
                pass
                
        elif "Assistant:" in line and hasattr(self, 'last_user_msg'):
            model_response = line.split("Assistant: ")[-1].strip()
            self.responses.append({
                'time': timestamp,
                'model': self.current_model,
                'turn': self.current_turn,
                'user_msg': getattr(self, 'last_user_msg', 'Unknown'),
                'model_response': model_response,
                'reification': None
            })
            
        elif "REIFICATION DETECTED" in line:
            self.reifications_detected += 1
            if self.responses:
                self.responses[-1]['reification'] = line.split("REIFICATION DETECTED: ")[-1].strip()
                
        elif "Completed sequence" in line:
            self.sequences_completed += 1
            
        elif "Model evaluation complete" in line:
            self.models_completed += 1
            
        elif "Failed to evaluate" in line:
            self.models_failed += 1

def run_benchmark_with_dashboard(models_to_test):
    """Run benchmark while displaying live dashboard"""
    dashboard = LiveBenchmarkDashboard()
    dashboard.total_sequences = len(models_to_test) * 5  # 5 sequences per model in quick test
    
    # Start benchmark process
    cmd = [
        "poetry", "run", "python", "run_quick_benchmark_verbose.py"
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Thread to read output
    def read_output():
        for line in process.stdout:
            dashboard.update_from_log(line)
            
    reader_thread = threading.Thread(target=read_output)
    reader_thread.daemon = True
    reader_thread.start()
    
    # Display loop
    try:
        while process.poll() is None:
            dashboard.display()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopped monitoring. Benchmark continues in background...")
        
    return process

if __name__ == "__main__":
    # Quick test models
    test_models = [
        {"provider": "anthropic", "model": "claude-3-haiku-20240307"},
        {"provider": "openai", "model": "gpt-4o-mini-2024-07-18"},
        {"provider": "openrouter", "model": "deepseek/deepseek-chat:free"},
        {"provider": "google", "model": "gemini-2.0-flash"},
    ]
    
    print("Starting Live Benchmark Dashboard...")
    print("This will run a quick test with 4 models, 5 sequences each")
    print("Press Enter to start...")
    input()
    
    process = run_benchmark_with_dashboard(test_models)
    
    # Wait for completion
    process.wait()
    print("\n✅ Benchmark Complete!")