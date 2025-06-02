#!/usr/bin/env python3
"""
Verbose real-time benchmark with live output
"""

import os
import sys
import logging
import json
from datetime import datetime

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

# Setup logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('benchmark_realtime.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Silence HTTP logs but keep our logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from model_interface import ModelFactory
from sequences_3_turn import get_3_turn_sequences
from multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3
from scoring_evaluator import ModelScoringEvaluator

def run_single_model_verbose(provider, model_name, max_sequences=5):
    """Run benchmark on single model with verbose output"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING: {provider}/{model_name}")
    logger.info(f"{'='*80}")
    
    # Create model
    try:
        model = ModelFactory.create(provider, model_name)
        logger.info("✓ Model initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize model: {e}")
        return
    
    # Create scoring model
    try:
        scoring_interface = ModelFactory.create("openai", "gpt-4.1-2025-04-14")
        scoring_model = ModelScoringEvaluator(scoring_interface)
        logger.info("✓ Scoring model initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize scoring: {e}")
        return
    
    # Get sequences
    sequences = get_3_turn_sequences()[:max_sequences]
    logger.info(f"✓ Testing {len(sequences)} sequences")
    
    # Create evaluator
    evaluator = MultiTurnEvaluatorV3(
        model_interface=model,
        scoring_model_interface=scoring_interface,
        scoring_evaluator=scoring_model
    )
    
    results = []
    
    for i, sequence in enumerate(sequences, 1):
        logger.info(f"\n--- Sequence {i}/{len(sequences)}: {sequence.id} ---")
        logger.info(f"Category: {sequence.category.value}")
        logger.info(f"Description: {sequence.description}")
        
        try:
            # Process each turn
            conversation_history = []
            sequence_result = {
                "sequence_id": sequence.id,
                "turns": [],
                "reification_occurred": False
            }
            
            for turn_num, turn in enumerate(sequence.turns):
                logger.info(f"\n[Turn {turn_num + 1}]")
                logger.info(f"User: {turn.prompt[:150]}...")
                
                # Get model response
                start_time = datetime.now()
                model_response = model.query(turn.prompt)
                response_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"Model ({response_time:.1f}s): {model_response[:150]}...")
                
                # Score for reification
                logger.info("Scoring response...")
                conversation_history.append({
                    "role": "user",
                    "content": turn.prompt
                })
                conversation_history.append({
                    "role": "assistant", 
                    "content": model_response
                })
                
                scoring_prompt = evaluator._create_reification_scoring_prompt(
                    turn_num + 1,
                    turn.prompt,
                    model_response,
                    conversation_history
                )
                
                scoring_response = scoring_model.scoring_model.query(scoring_prompt)
                
                # Parse scoring
                try:
                    analysis = json.loads(scoring_response)
                    reification_detected = analysis.get('reification_detected', False)
                    
                    if reification_detected:
                        logger.warning(f"⚠️  REIFICATION DETECTED!")
                        logger.warning(f"   Reasoning: {analysis.get('reasoning', 'No reason given')}")
                        logger.warning(f"   Severity: {analysis.get('severity', 'unknown')}")
                        sequence_result["reification_occurred"] = True
                    else:
                        logger.info("✓ No reification detected")
                        
                except Exception as e:
                    logger.error(f"Failed to parse scoring: {e}")
                
                sequence_result["turns"].append({
                    "turn": turn_num + 1,
                    "user": turn.prompt,
                    "model": model_response,
                    "response_time": response_time,
                    "reification": reification_detected if 'reification_detected' in locals() else None
                })
            
            results.append(sequence_result)
            logger.info(f"\n✓ Completed sequence: {sequence.id}")
            logger.info(f"  Reification: {'YES' if sequence_result['reification_occurred'] else 'NO'}")
            
        except Exception as e:
            logger.error(f"✗ Error in sequence {sequence.id}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Model: {provider}/{model_name}")
    logger.info(f"Sequences tested: {len(results)}")
    reif_count = sum(1 for r in results if r["reification_occurred"])
    logger.info(f"Reifications: {reif_count}/{len(results)} ({reif_count/len(results)*100:.1f}%)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results_v3/verbose_{model_name.replace('/', '_')}_{timestamp}.json"
    os.makedirs("results_v3", exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump({
            "model": model_name,
            "provider": provider,
            "timestamp": timestamp,
            "results": results
        }, f, indent=2)
    
    logger.info(f"\nResults saved to: {filename}")

def main():
    """Test a few models with verbose output"""
    
    # Test models - start with fast ones
    test_models = [
        ("anthropic", "claude-3-haiku-20240307"),  # Fast
        ("openai", "gpt-4o-mini-2024-07-18"),      # Fast
        ("anthropic", "claude-opus-4-20250514"),    # Slow - will show progress
    ]
    
    logger.info("SCHIZOBENCH VERBOSE REAL-TIME TEST")
    logger.info(f"Started: {datetime.now()}")
    logger.info(f"Testing {len(test_models)} models with 5 sequences each")
    
    for provider, model in test_models:
        try:
            run_single_model_verbose(provider, model, max_sequences=5)
        except KeyboardInterrupt:
            logger.info("\n\nBenchmark interrupted by user")
            break
        except Exception as e:
            logger.error(f"Failed to test {provider}/{model}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()