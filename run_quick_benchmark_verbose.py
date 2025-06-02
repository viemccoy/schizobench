#!/usr/bin/env python3
"""
Verbose Quick Benchmark - Outputs detailed progress for dashboard
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# Setup verbose logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simple format for parsing
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Silence HTTP logs
logging.getLogger("httpx").setLevel(logging.WARNING)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from model_interface import ModelFactory
from multi_turn_sequences_library import MultiTurnSequenceLibraryV3
from multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3
from scoring_evaluator import ModelScoringEvaluator

# Quick test configuration
QUICK_MODELS = [
    {"provider": "anthropic", "model": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
    {"provider": "openai", "model": "gpt-4o-mini-2024-07-18", "name": "GPT-4o Mini"},
    {"provider": "openrouter", "model": "deepseek/deepseek-chat:free", "name": "DeepSeek Chat"},
    {"provider": "google", "model": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
]

def run_verbose_benchmark():
    """Run benchmark with verbose output for dashboard"""
    logger.info("=== SCHIZOBENCH v3.0 VERBOSE BENCHMARK ===")
    logger.info(f"Started: {datetime.now()}")
    logger.info(f"Testing {len(QUICK_MODELS)} models with 5 sequences each")
    
    # Initialize components
    sequence_library = MultiTurnSequenceLibraryV3()
    all_sequences = sequence_library.get_sequences(
        lengths=[3],  # Only 3-turn for quick test
        categories=None,
        limit=5  # Only 5 sequences
    )
    
    logger.info(f"Loaded {len(all_sequences)} test sequences")
    
    # Initialize scoring model (use GPT-4.1 for accurate reification detection)
    scoring_interface = ModelFactory.create("openai", "gpt-4.1-2025-04-14")
    scoring_model = ModelScoringEvaluator(scoring_interface)
    
    results_dir = "results_v3_verbose"
    os.makedirs(results_dir, exist_ok=True)
    
    all_results = []
    
    for model_config in QUICK_MODELS:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing model: {model_config['name']} ({model_config['provider']}/{model_config['model']})")
        logger.info(f"{'='*60}")
        
        try:
            # Create model
            model = ModelFactory.create(
                provider=model_config['provider'],
                model_name=model_config['model'],
                temperature=0.7
            )
            
            # Create evaluator
            evaluator = MultiTurnEvaluatorV3(
                model=model,
                scoring_model=scoring_model,
                verbose=True  # Enable verbose output
            )
            
            model_results = {
                "model": model_config['model'],
                "provider": model_config['provider'],
                "sequences": []
            }
            
            # Evaluate sequences
            for i, sequence in enumerate(all_sequences, 1):
                logger.info(f"\nEvaluating sequence: {sequence.id} ({i}/{len(all_sequences)})")
                logger.info(f"Category: {sequence.category.value}")
                logger.info(f"Description: {sequence.description}")
                
                # Run evaluation
                result = evaluator.evaluate_sequence(sequence)
                
                # Log each turn
                for j, turn in enumerate(result.turns):
                    logger.info(f"\nTurn {j+1}:")
                    logger.info(f"User: {turn.user_message[:200]}...")
                    logger.info(f"Assistant: {turn.model_response[:200]}...")
                    
                    if turn.reification_analysis:
                        if turn.reification_analysis.get('reification_detected'):
                            logger.info(f"⚠️ REIFICATION DETECTED: {turn.reification_analysis.get('reasoning', 'No reasoning provided')}")
                            logger.info(f"Severity: {turn.reification_analysis.get('severity', 'Unknown')}")
                
                logger.info(f"\nCompleted sequence: {sequence.id}")
                logger.info(f"Reification detected: {'Yes' if result.reification_occurred else 'No'}")
                
                model_results["sequences"].append({
                    "id": sequence.id,
                    "reification": result.reification_occurred,
                    "first_turn": result.first_reification_turn
                })
                
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{results_dir}/verbose_{model_config['model'].replace('/', '_')}_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(model_results, f, indent=2)
                
            logger.info(f"\nModel evaluation complete: {model_config['name']}")
            logger.info(f"Results saved to: {filename}")
            
            all_results.append(model_results)
            
        except Exception as e:
            logger.error(f"\nFailed to evaluate {model_config['name']}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("BENCHMARK COMPLETE")
    logger.info("="*60)
    
    total_reifications = sum(
        sum(1 for seq in model["sequences"] if seq["reification"])
        for model in all_results
    )
    
    logger.info(f"Total models tested: {len(all_results)}")
    logger.info(f"Total sequences: {len(all_results) * len(all_sequences)}")
    logger.info(f"Total reifications: {total_reifications}")
    
    # Model summary
    for model in all_results:
        reif_count = sum(1 for seq in model["sequences"] if seq["reification"])
        reif_rate = (reif_count / len(model["sequences"]) * 100) if model["sequences"] else 0
        logger.info(f"\n{model['provider']}/{model['model']}:")
        logger.info(f"  Reification rate: {reif_rate:.1f}% ({reif_count}/{len(model['sequences'])})")

if __name__ == "__main__":
    run_verbose_benchmark()