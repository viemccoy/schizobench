#!/usr/bin/env python3
"""
Test verbose output with a single model and sequence
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Silence HTTP logs
logging.getLogger("httpx").setLevel(logging.WARNING)

from model_interface import ModelFactory
from sequences_3_turn import get_3_turn_sequences
from multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3
from scoring_evaluator import ModelScoringEvaluator

def test_single_sequence():
    """Test one sequence with verbose output"""
    logger.info("=== VERBOSE OUTPUT TEST ===")
    
    # Get one sequence
    sequences = get_3_turn_sequences()
    test_sequence = sequences[0]
    
    logger.info(f"\nTest Sequence: {test_sequence.id}")
    logger.info(f"Category: {test_sequence.category.value}")
    logger.info(f"Description: {test_sequence.description}")
    
    # Create model
    logger.info("\nInitializing model...")
    model = ModelFactory.create("openai", "gpt-4o-mini-2024-07-18")
    
    # Create scoring model interface
    scoring_interface = ModelFactory.create("openai", "gpt-4.1-2025-04-14")
    scoring_model = ModelScoringEvaluator(scoring_interface)
    
    # Create evaluator
    evaluator = MultiTurnEvaluatorV3(model, scoring_model, verbose=True)
    
    logger.info("\nStarting evaluation...")
    logger.info("-" * 60)
    
    # Evaluate
    result = evaluator.evaluate_sequence(test_sequence)
    
    # Show results
    logger.info("\n" + "-" * 60)
    logger.info("EVALUATION COMPLETE")
    logger.info(f"Reification occurred: {'YES' if result.reification_occurred else 'NO'}")
    if result.reification_occurred:
        logger.info(f"First reification at turn: {result.first_reification_turn}")
        logger.info(f"Severity: {result.max_severity}")
    
    # Show each turn
    for i, turn in enumerate(result.turns):
        logger.info(f"\nTurn {i+1} Summary:")
        logger.info(f"  User: {turn.user_message[:100]}...")
        logger.info(f"  Model: {turn.model_response[:100]}...")
        if turn.reification_analysis and turn.reification_analysis.get('reification_detected'):
            logger.info(f"  ⚠️ REIFICATION: {turn.reification_analysis.get('reasoning', '')[:100]}...")

if __name__ == "__main__":
    test_single_sequence()