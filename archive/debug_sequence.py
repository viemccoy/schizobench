#!/usr/bin/env python3
"""
Debug script to help understand sequence handling issues in SchizoBench
"""

import logging
from schizobench.multi_turn_sequences_v3 import MultiTurnSequenceLibraryV3
from schizobench.multi_turn_evaluator_v3 import MultiTurnEvaluatorV3
from schizobench.scoring_evaluator import ModelScoringEvaluator
from schizobench.model_interface import MockInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run test to debug sequence handling"""
    
    # Load sequences
    logger.info("Loading sequences...")
    sequences = MultiTurnSequenceLibraryV3.get_all_sequences()
    
    # Setup mock evaluator
    logger.info("Setting up evaluator...")
    mock_model = MockInterface()
    evaluator = ModelScoringEvaluator(None)  # Pattern-based evaluator
    multi_turn_evaluator = MultiTurnEvaluatorV3(evaluator)
    
    # Try to evaluate first sequence
    sequence = sequences[0]
    logger.info(f"Testing sequence: {sequence.id} - {sequence.title}")
    logger.info(f"Sequence type: {type(sequence)}")
    logger.info(f"Category type: {type(sequence.category)}")
    
    # Create a dictionary version
    logger.info("Creating dictionary version...")
    seq_dict = {
        'id': sequence.id,
        'title': sequence.title,
        'category': sequence.category,
        'vulnerability_pattern': sequence.vulnerability_pattern,
        'turns': sequence.turns,
        'critical_transitions': sequence.critical_transitions,
        'reification_turns': sequence.reification_turns,
        'expected_arc': sequence.expected_arc,
        'description': 'Test description'
    }
    
    # Serialize and deserialize to ensure we're dealing with plain dictionaries
    import json
    logger.info("Serializing and deserializing sequence...")
    try:
        # This will fail because enums aren't serializable
        serialized = json.dumps(seq_dict)
        logger.info("Standard serialization succeeded - unexpected!")
    except TypeError as e:
        logger.info(f"Standard serialization failed as expected: {e}")
        
    # Create a properly serializable version
    serializable_dict = {
        'id': sequence.id,
        'title': sequence.title,
        'category': sequence.category.name,  # Use name instead of enum
        'vulnerability_pattern': sequence.vulnerability_pattern,
        'turns': [
            {
                'turn_number': t.turn_number,
                'prompt': t.prompt,
                'intent': t.intent.name,  # Use name instead of enum
                'expected_boundary': t.expected_boundary,
                'risk_factors': t.risk_factors
            }
            for t in sequence.turns
        ],
        'critical_transitions': sequence.critical_transitions,
        'reification_turns': sequence.reification_turns,
        'expected_arc': sequence.expected_arc
    }
    
    # This should work
    logger.info("Testing serializable dictionary...")
    try:
        serialized = json.dumps(serializable_dict)
        logger.info(f"Serialization succeeded! Length: {len(serialized)}")
    except Exception as e:
        logger.error(f"Serialization still failed: {e}")
    
    # Try to evaluate the sequence
    try:
        logger.info("Testing object evaluation...")
        result = multi_turn_evaluator.evaluate_sequence(
            mock_model, 
            sequence,
            None
        )
        logger.info("Sequence object evaluation succeeded!")
    except Exception as e:
        logger.error(f"Sequence object evaluation failed: {e}")
    
    # Try to evaluate the dictionary
    try:
        logger.info("Testing dictionary evaluation...")
        result = multi_turn_evaluator.evaluate_sequence(
            mock_model, 
            seq_dict,
            None
        )
        logger.info("Dictionary evaluation succeeded!")
    except Exception as e:
        logger.error(f"Dictionary evaluation failed: {e}")

if __name__ == "__main__":
    main()