#!/usr/bin/env python3
"""
Enhanced benchmark runner with live logging of model responses.
Shows each turn and scoring result as it happens.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
import os

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from {env_path}")
else:
    load_dotenv()  # Try default locations

from multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3 as MultiTurnEvaluator
from multi_turn_base import MultiTurnSequenceV3 as TestSequence

# ANSI colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_live(message: str, color: str = Colors.ENDC):
    """Print with immediate flush for live output."""
    print(f"{color}{message}{Colors.ENDC}")
    sys.stdout.flush()

class LiveMultiTurnEvaluator(MultiTurnEvaluator):
    """Extended evaluator that shows live progress."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_sequence = None
        self.current_turn = 0
    
    def evaluate_sequence(self, sequence: TestSequence) -> Dict:
        """Override to add live logging."""
        self.current_sequence = sequence.id
        self.current_turn = 0
        
        print_live(f"\n{'='*80}", Colors.HEADER)
        print_live(f"Starting: {sequence.id} ({sequence.category})", Colors.BOLD)
        print_live(f"Model: {self.model_interface.model_name}", Colors.BOLD)
        print_live(f"Turns: {len(sequence.turns)}", Colors.BOLD)
        
        # Run the evaluation with live updates
        result = super().evaluate_sequence(sequence)
        
        # Show final result
        if result.reification_occurred:
            print_live(f"Result: REIFICATION DETECTED", Colors.RED + Colors.BOLD)
        else:
            print_live(f"Result: PASSED", Colors.GREEN + Colors.BOLD)
        
        return result
    
    def _get_model_response(self, messages: List[Dict[str, str]]) -> str:
        """Override to show live responses."""
        self.current_turn += 1
        
        # Show user message
        user_msg = messages[-1]['content']
        print_live(f"\nTurn {self.current_turn} - User:", Colors.YELLOW)
        if len(user_msg) > 200:
            print_live(f"  {user_msg[:200]}...", Colors.YELLOW)
        else:
            print_live(f"  {user_msg}", Colors.YELLOW)
        
        # Get model response
        print_live("  [Waiting for model response...]", Colors.CYAN)
        start_time = time.time()
        
        response = super()._get_model_response(messages)
        
        elapsed = time.time() - start_time
        print_live(f"\nTurn {self.current_turn} - {self.model_interface.model_name} ({elapsed:.1f}s):", Colors.BLUE)
        if len(response) > 300:
            print_live(f"  {response[:300]}...", Colors.BLUE)
        else:
            print_live(f"  {response}", Colors.BLUE)
        
        return response
    
    def _score_turn(self, turn_data: Dict) -> Dict:
        """Override to show live scoring."""
        print_live("  [Scoring response...]", Colors.CYAN)
        
        scoring = super()._score_turn(turn_data)
        
        if scoring['reification_detected']:
            severity = scoring.get('severity', 'unknown')
            print_live(f"  ⚠️  REIFICATION: {severity.upper()}", Colors.RED + Colors.BOLD)
            phrases = scoring.get('validation_phrases', [])
            if phrases:
                print_live(f"  Phrases: {', '.join(phrases[:2])}", Colors.RED)
        else:
            print_live(f"  ✓ Safe response", Colors.GREEN)
        
        return scoring

def run_live_benchmark(provider: str, model: str, sequences: Optional[List[str]] = None):
    """Run benchmark with live output."""
    print_live("SchizoBench v3.0 - Live Benchmark", Colors.HEADER + Colors.BOLD)
    print_live(f"Provider: {provider}", Colors.BOLD)
    print_live(f"Model: {model}", Colors.BOLD)
    print_live(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.BOLD)
    
    # Initialize model interfaces
    try:
        from model_interface import ModelFactory
        
        # Create the model interface (auto-loads API key from environment)
        model_interface = ModelFactory.create(
            provider=provider,
            model_name=model,
            temperature=0.7
        )
        
        # Create scoring model interface (always use GPT-4.1 for scoring)
        scoring_model_interface = ModelFactory.create(
            provider="openai",
            model_name="gpt-4.1-2025-04-14",
            temperature=0.3  # Lower temp for consistent scoring
        )
        
        # Initialize evaluator with both interfaces
        evaluator = LiveMultiTurnEvaluator(
            model_interface=model_interface,
            scoring_model_interface=scoring_model_interface
        )
    except Exception as e:
        print_live(f"Error initializing evaluator: {e}", Colors.RED)
        return
    
    # Load sequences
    from sequences_3_turn import get_3_turn_sequences
    from sequences_8_turn import get_8_turn_sequences
    from sequences_20_turn import get_20_turn_sequences
    
    all_sequences = get_3_turn_sequences() + get_8_turn_sequences() + get_20_turn_sequences()
    
    # Filter sequences if specified
    if sequences:
        all_sequences = [s for s in all_sequences if s.id in sequences]
        print_live(f"Running {len(all_sequences)} specified sequences", Colors.BOLD)
    else:
        print_live(f"Running all {len(all_sequences)} sequences", Colors.BOLD)
    
    # Create results directory
    results_dir = Path("results_v3")
    results_dir.mkdir(exist_ok=True)
    
    # Track statistics
    stats = {
        'total': 0,
        'completed': 0,
        'failed': 0,
        'errors': 0,
        'reifications': 0
    }
    
    start_time = time.time()
    
    # Run each sequence
    for i, sequence in enumerate(all_sequences):
        stats['total'] += 1
        
        try:
            # Show progress
            print_live(f"\n[{i+1}/{len(all_sequences)}] {stats['reifications']}/{stats['completed']} reifications so far", Colors.CYAN)
            
            # Evaluate sequence
            result = evaluator.evaluate_sequence(sequence)
            
            # Convert result to dictionary for saving
            result_dict = {
                'model': model,
                'provider': provider,
                'sequence_id': result.sequence_id,
                'category': result.category.value if hasattr(result.category, 'value') else str(result.category),
                'reification_detected': result.reification_occurred,
                'reification_locations': result.reification_locations,
                'boundary_persistence_score': result.boundary_persistence_score,
                'overall_risk': result.overall_risk.value if hasattr(result.overall_risk, 'value') else str(result.overall_risk),
                'timestamp': datetime.now().isoformat(),
                'turns': []
            }
            
            # Add turn data
            for turn in result.turns:
                turn_dict = {
                    'turn_number': turn.turn_number,
                    'user': turn.prompt,
                    'assistant': turn.response,
                    'risk_score': turn.risk_score.value if hasattr(turn.risk_score, 'value') else str(turn.risk_score),
                    'maintained_boundary': turn.maintained_boundary,
                    'reification_failure': turn.reification_failure,
                    'response_time': turn.response_time,
                    'scoring': turn.reification_analysis if turn.reification_analysis else {}
                }
                result_dict['turns'].append(turn_dict)
            
            # Save result
            result_file = results_dir / f"{model}_{sequence.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(result_file, 'w') as f:
                json.dump(result_dict, f, indent=2)
            
            stats['completed'] += 1
            if result.reification_occurred:
                stats['reifications'] += 1
            
        except Exception as e:
            import traceback
            print_live(f"Error in sequence {sequence.id}: {e}", Colors.RED)
            print_live(f"Traceback: {traceback.format_exc()}", Colors.RED)
            stats['errors'] += 1
            continue
    
    # Final statistics
    elapsed = time.time() - start_time
    print_live(f"\n{'='*80}", Colors.HEADER)
    print_live("Benchmark Complete!", Colors.HEADER + Colors.BOLD)
    print_live(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)", Colors.BOLD)
    print_live(f"Sequences: {stats['completed']}/{stats['total']}", Colors.BOLD)
    print_live(f"Errors: {stats['errors']}", Colors.BOLD)
    
    if stats['completed'] > 0:
        reification_rate = (stats['reifications'] / stats['completed']) * 100
        color = Colors.GREEN if reification_rate < 10 else Colors.YELLOW if reification_rate < 30 else Colors.RED
        print_live(f"Reification Rate: {reification_rate:.1f}% ({stats['reifications']}/{stats['completed']})", color + Colors.BOLD)
    
    print_live(f"\nResults saved to: {results_dir.absolute()}", Colors.CYAN)

def main():
    parser = argparse.ArgumentParser(description='Run SchizoBench v3.0 with live output')
    parser.add_argument('--provider', required=True, choices=['anthropic', 'openai', 'google', 'openrouter'],
                        help='Model provider')
    parser.add_argument('--model', required=True, help='Model name')
    parser.add_argument('--sequences', nargs='+', help='Specific sequence IDs to run (optional)')
    
    args = parser.parse_args()
    
    run_live_benchmark(args.provider, args.model, args.sequences)

if __name__ == "__main__":
    main()