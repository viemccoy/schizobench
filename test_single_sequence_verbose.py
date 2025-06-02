#!/usr/bin/env python3
"""
Test a single sequence with full verbose output
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from model_interface import ModelFactory
from sequences_3_turn import get_3_turn_sequences
from multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3
from scoring_evaluator import ModelScoringEvaluator

# Test with one fast model
model_name = "openai/gpt-4o-mini-2024-07-18"
print(f"Testing {model_name}")
print("="*60)

# Create model
model = ModelFactory.create("openai", "gpt-4o-mini-2024-07-18")
print("✓ Model initialized")

# Create scoring interface and evaluator
scoring_interface = ModelFactory.create("openai", "gpt-4.1-2025-04-14")
scoring_evaluator = ModelScoringEvaluator(scoring_interface)
print("✓ Scoring model initialized")

# Create evaluator
evaluator = MultiTurnEvaluatorV3(
    model_interface=model,
    scoring_model_interface=scoring_interface,
    scoring_evaluator=scoring_evaluator
)
print("✓ Evaluator created")

# Get one sequence
sequence = get_3_turn_sequences()[0]
print(f"\nTesting sequence: {sequence.id}")
print(f"Category: {sequence.category.value}")
print(f"Description: {sequence.description}")
print("-"*60)

# Evaluate with timing
start_time = time.time()
result = evaluator.evaluate_sequence(sequence)
elapsed = time.time() - start_time

print(f"\n✓ Evaluation complete in {elapsed:.1f} seconds")
print("-"*60)

# Show results
print(f"Reification occurred: {'YES' if result.reification_occurred else 'NO'}")
if result.reification_occurred:
    # Find first reification turn
    first_turn = None
    for i, turn in enumerate(result.turns):
        if turn.reification_analysis and turn.reification_analysis.get('reification_detected'):
            first_turn = i + 1
            break
    if first_turn:
        print(f"First reification at turn: {first_turn}")
    
    # Get max severity
    severities = []
    for turn in result.turns:
        if turn.reification_analysis and turn.reification_analysis.get('severity'):
            severities.append(turn.reification_analysis['severity'])
    if severities:
        print(f"Severities detected: {', '.join(severities)}")

# Show each turn
print("\nTurn-by-turn results:")
for i, turn in enumerate(result.turns):
    print(f"\n[Turn {i+1}]")
    print(f"User: {turn.user[:100]}...")
    print(f"Model: {turn.assistant[:150]}...")
    
    if turn.reification_analysis:
        if turn.reification_analysis.get('reification_detected'):
            print(f"⚠️  REIFICATION DETECTED!")
            print(f"   Reasoning: {turn.reification_analysis.get('reasoning', '')[:200]}...")
            print(f"   Severity: {turn.reification_analysis.get('severity')}")
        else:
            print("✓ No reification")

# Save result
os.makedirs("results_v3", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"results_v3/single_test_{timestamp}.json"

with open(filename, 'w') as f:
    json.dump({
        "model": model_name,
        "sequence": sequence.id,
        "elapsed_time": elapsed,
        "reification_occurred": result.reification_occurred,
        "turns": [
            {
                "turn": i+1,
                "user": turn.user_message,
                "model": turn.model_response,
                "reification": turn.reification_analysis
            }
            for i, turn in enumerate(result.turns)
        ]
    }, f, indent=2)

print(f"\nResults saved to: {filename}")