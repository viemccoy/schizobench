#!/usr/bin/env python3
"""
Live monitoring script for SchizoBench v3.0 results.
Shows real-time model responses and reification scoring as they come in.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def format_severity(severity: str) -> str:
    """Color-code severity levels."""
    colors = {
        'none': Colors.GREEN,
        'mild': Colors.CYAN,
        'moderate': Colors.YELLOW,
        'severe': Colors.RED,
        'critical': Colors.RED + Colors.BOLD
    }
    color = colors.get(severity.lower(), Colors.ENDC)
    return f"{color}{severity.upper()}{Colors.ENDC}"

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except:
        return timestamp

def display_conversation(result: Dict, show_full: bool = False):
    """Display a single conversation result."""
    model = result.get('model', 'Unknown')
    sequence = result.get('sequence_id', 'Unknown')
    category = result.get('category', 'Unknown')
    reification_detected = result.get('reification_detected', False)
    
    # Header
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}Model:{Colors.ENDC} {model}")
    print(f"{Colors.BOLD}Sequence:{Colors.ENDC} {sequence} ({category})")
    print(f"{Colors.BOLD}Time:{Colors.ENDC} {format_timestamp(result.get('timestamp', ''))}")
    
    # Reification status
    if reification_detected:
        print(f"{Colors.BOLD}Status:{Colors.ENDC} {Colors.RED}REIFICATION DETECTED{Colors.ENDC}")
    else:
        print(f"{Colors.BOLD}Status:{Colors.ENDC} {Colors.GREEN}PASSED{Colors.ENDC}")
    
    # Show conversation turns
    turns = result.get('turns', [])
    print(f"\n{Colors.BOLD}Conversation ({len(turns)} turns):{Colors.ENDC}")
    
    for i, turn in enumerate(turns):
        print(f"\n{Colors.CYAN}Turn {i+1}:{Colors.ENDC}")
        
        # User message
        user_msg = turn.get('user', '')
        if show_full or len(user_msg) <= 100:
            print(f"  {Colors.YELLOW}User:{Colors.ENDC} {user_msg}")
        else:
            print(f"  {Colors.YELLOW}User:{Colors.ENDC} {user_msg[:100]}...")
        
        # Model response
        model_msg = turn.get('assistant', '')
        if show_full or len(model_msg) <= 200:
            print(f"  {Colors.BLUE}Model:{Colors.ENDC} {model_msg}")
        else:
            print(f"  {Colors.BLUE}Model:{Colors.ENDC} {model_msg[:200]}...")
        
        # Scoring for this turn
        scoring = turn.get('scoring', {})
        if scoring.get('reification_detected'):
            severity = scoring.get('severity', 'unknown')
            phrases = scoring.get('validation_phrases', [])
            print(f"  {Colors.RED}⚠️  Reification: {format_severity(severity)}{Colors.ENDC}")
            if phrases and show_full:
                print(f"  {Colors.RED}Phrases: {', '.join(phrases[:3])}{Colors.ENDC}")

def monitor_results(results_dir: str = "results_v3", interval: int = 5, show_full: bool = False):
    """Monitor results directory for new completions."""
    results_path = Path(results_dir)
    seen_files = set()
    
    print(f"{Colors.HEADER}SchizoBench v3.0 Live Monitor{Colors.ENDC}")
    print(f"Watching: {results_path.absolute()}")
    print(f"Refresh: Every {interval} seconds")
    print(f"Mode: {'Full conversations' if show_full else 'Abbreviated'}")
    print("\nPress Ctrl+C to stop monitoring\n")
    
    # Stats tracking
    stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'by_model': {},
        'by_category': {}
    }
    
    try:
        while True:
            # Check for new result files
            if results_path.exists():
                for file_path in results_path.glob("*.json"):
                    if file_path.name not in seen_files:
                        seen_files.add(file_path.name)
                        
                        try:
                            with open(file_path, 'r') as f:
                                result = json.load(f)
                            
                            # Update stats
                            model = result.get('model', 'Unknown')
                            category = result.get('category', 'Unknown')
                            reification = result.get('reification_detected', False)
                            
                            stats['total'] += 1
                            if reification:
                                stats['failed'] += 1
                            else:
                                stats['passed'] += 1
                            
                            # Track by model
                            if model not in stats['by_model']:
                                stats['by_model'][model] = {'total': 0, 'failed': 0}
                            stats['by_model'][model]['total'] += 1
                            if reification:
                                stats['by_model'][model]['failed'] += 1
                            
                            # Track by category
                            if category not in stats['by_category']:
                                stats['by_category'][category] = {'total': 0, 'failed': 0}
                            stats['by_category'][category]['total'] += 1
                            if reification:
                                stats['by_category'][category]['failed'] += 1
                            
                            # Display the conversation
                            display_conversation(result, show_full)
                            
                            # Show running stats
                            print(f"\n{Colors.BOLD}Running Stats:{Colors.ENDC}")
                            print(f"  Total: {stats['total']} | Passed: {stats['passed']} | Failed: {stats['failed']}")
                            fail_rate = (stats['failed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                            print(f"  Overall Reification Rate: {fail_rate:.1f}%")
                            
                        except Exception as e:
                            print(f"{Colors.RED}Error reading {file_path.name}: {e}{Colors.ENDC}")
            
            # Brief summary every iteration
            if stats['total'] > 0:
                print(f"\n{Colors.CYAN}[{datetime.now().strftime('%H:%M:%S')}] Monitoring... {stats['total']} results processed{Colors.ENDC}", end='\r')
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.HEADER}Final Statistics:{Colors.ENDC}")
        print(f"Total Sequences: {stats['total']}")
        print(f"Passed: {stats['passed']} ({stats['passed']/stats['total']*100:.1f}%)")
        print(f"Failed: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
        
        # Model breakdown
        print(f"\n{Colors.BOLD}By Model:{Colors.ENDC}")
        for model, data in sorted(stats['by_model'].items()):
            rate = (data['failed'] / data['total'] * 100) if data['total'] > 0 else 0
            status = Colors.GREEN if rate < 10 else Colors.YELLOW if rate < 30 else Colors.RED
            print(f"  {model}: {data['failed']}/{data['total']} failed ({status}{rate:.1f}%{Colors.ENDC})")
        
        # Category breakdown
        print(f"\n{Colors.BOLD}By Category:{Colors.ENDC}")
        for category, data in sorted(stats['by_category'].items()):
            rate = (data['failed'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  {category}: {data['failed']}/{data['total']} failed ({rate:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Monitor SchizoBench v3.0 results in real-time')
    parser.add_argument('--dir', default='results_v3', help='Results directory to monitor')
    parser.add_argument('--interval', type=int, default=5, help='Refresh interval in seconds')
    parser.add_argument('--full', action='store_true', help='Show full conversations (not abbreviated)')
    
    args = parser.parse_args()
    
    monitor_results(args.dir, args.interval, args.full)

if __name__ == "__main__":
    main()