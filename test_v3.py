#!/usr/bin/env python3
"""
Quick test script for SchizoBench v3.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schizobench.model_interface import ModelFactory
from schizobench.multi_turn_sequences_v3 import MultiTurnSequenceLibraryV3
from schizobench.multi_turn_evaluator_v3 import MultiTurnEvaluatorV3
from schizobench.scoring_evaluator import ModelScoringEvaluator
from schizobench.types import ResponseRisk
import logging

logging.basicConfig(level=logging.INFO)


def test_v3():
    """Test basic v3 functionality"""
    print("Testing SchizoBench v3.0...")
    
    # Test sequences
    print("\n1. Testing sequence library...")
    sequences_3 = MultiTurnSequenceLibraryV3.get_3_turn_sequences()
    sequences_8 = MultiTurnSequenceLibraryV3.get_8_turn_sequences()
    sequences_20 = MultiTurnSequenceLibraryV3.get_20_turn_sequences()
    
    print(f"   - 3-turn sequences: {len(sequences_3)}")
    print(f"   - 8-turn sequences: {len(sequences_8)}")
    print(f"   - 20-turn sequences: {len(sequences_20)}")
    print(f"   - Total sequences: {len(sequences_3) + len(sequences_8) + len(sequences_20)}")
    
    # Test with mock model
    print("\n2. Testing with mock model...")
    model = ModelFactory.create(provider='mock', model_name='mock-model')
    
    # Create a simple pattern-based evaluator wrapper
    class SimplePatternEvaluator:
        def evaluate_response(self, response, prompt):
            # Simple pattern matching for testing
            response_lower = response.lower()
            if "chosen" in response_lower or "special" in response_lower:
                return ResponseRisk.CRITICAL, ["validates delusion"], [], True
            else:
                return ResponseRisk.SAFE, [], ["appropriate response"], False
    
    evaluator = SimplePatternEvaluator()
    multi_turn_eval = MultiTurnEvaluatorV3(evaluator)
    
    # Test one 3-turn sequence
    test_seq = sequences_3[0]
    print(f"\n3. Testing sequence: {test_seq.id}")
    print(f"   - Title: {test_seq.title}")
    print(f"   - Category: {test_seq.category.value}")
    print(f"   - Vulnerability: {test_seq.vulnerability_pattern}")
    
    result = multi_turn_eval.evaluate_sequence(model, test_seq)
    
    print(f"\n4. Results:")
    print(f"   - Overall risk: {result.overall_risk.name}")
    print(f"   - Reification occurred: {result.reification_occurred}")
    print(f"   - Boundary persistence: {result.boundary_persistence_score:.1f}%")
    print(f"   - Risk progression: {[r.name for r in result.risk_escalation_pattern]}")
    
    # Test dynamic prompt generation
    print("\n5. Testing dynamic prompt generation...")
    dynamic_seq = None
    for seq in sequences_8:
        if any(turn.dynamic_prompt_generator for turn in seq.turns):
            dynamic_seq = seq
            break
    
    if dynamic_seq:
        print(f"   - Found sequence with dynamic prompts: {dynamic_seq.id}")
        # Test the dynamic prompt generator
        history = [("Test prompt", "Test response with fiction mentioned")]
        for turn in dynamic_seq.turns:
            if turn.dynamic_prompt_generator:
                dynamic_prompt = turn.dynamic_prompt_generator(history)
                print(f"   - Generated prompt: {dynamic_prompt[:50]}...")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_v3()