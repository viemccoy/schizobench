#!/usr/bin/env python3
"""
Robust SchizoBench v3.0 Runner with enhanced error handling and progress logging
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Log startup immediately
logger.info("=" * 70)
logger.info("SchizoBench v3.0 Starting Up")
logger.info(f"Time: {datetime.now().isoformat()}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info("=" * 70)

# Try imports with error handling
try:
    logger.info("Loading dependencies...")
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✓ Environment variables loaded")
    
    from model_interface import ModelFactory
    logger.info("✓ ModelFactory imported")
    
    from multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3
    logger.info("✓ MultiTurnEvaluatorV3 imported")
    
    from scoring_evaluator import ModelScoringEvaluator
    logger.info("✓ ModelScoringEvaluator imported")
    
    import multi_turn_sequences_library as library
    logger.info("✓ Sequences library imported")
    
    from schizo_types import RiskCategory, ResponseRisk
    logger.info("✓ Types imported")
    
    try:
        from visualizer import SchizoBenchVisualizer as Visualizer
        logger.info("✓ Visualizer imported")
    except ImportError:
        logger.warning("Visualizer not available - skipping visualization")
        Visualizer = None
    
except ImportError as e:
    logger.error(f"Failed to import required module: {e}")
    logger.error("Please ensure all dependencies are installed with: poetry install")
    sys.exit(1)


class SchizoBenchV3Runner:
    """Enhanced v3.0 benchmark runner with robust error handling"""
    
    def __init__(self, args):
        self.args = args
        self.results_dir = Path(args.results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize models with error handling
        logger.info("\nInitializing models...")
        
        try:
            # Get system prompt if provided
            self.system_prompt = None
            if args.system_prompt:
                self.system_prompt = args.system_prompt
                logger.info(f"Using custom system prompt: {self.system_prompt[:50]}...")
            
            # Initialize main model
            logger.info(f"Creating {args.provider}/{args.model} interface...")
            self.model = ModelFactory.create(
                provider=args.provider,
                model_name=args.model,
                temperature=args.temperature
            )
            logger.info(f"✓ Main model initialized: {args.provider}/{args.model}")
            
            # Initialize scoring model
            logger.info(f"Creating scoring model {args.scoring_provider}/{args.scoring_model}...")
            self.scoring_model = ModelFactory.create(
                provider=args.scoring_provider,
                model_name=args.scoring_model,
                temperature=0.3  # Lower temperature for consistent scoring
            )
            logger.info(f"✓ Scoring model initialized: {args.scoring_provider}/{args.scoring_model}")
            
            # Test models with a simple query
            logger.info("Testing model connectivity...")
            test_response = self.model.query("Hello, please respond with 'OK'")
            if test_response:
                logger.info(f"✓ Main model responding: {test_response[:50]}...")
            else:
                raise ValueError("Main model returned empty response")
                
            test_scoring = self.scoring_model.query("Respond with OK")
            if test_scoring:
                logger.info(f"✓ Scoring model responding: {test_scoring[:50]}...")
            else:
                raise ValueError("Scoring model returned empty response")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            logger.error(f"Full error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
        
        # Initialize evaluators
        try:
            logger.info("\nInitializing evaluators...")
            self.scoring_evaluator = ModelScoringEvaluator(
                scoring_model_interface=self.scoring_model
            )
            logger.info("✓ Scoring evaluator initialized")
            
            self.multi_turn_evaluator = MultiTurnEvaluatorV3(
                model_interface=self.model,
                scoring_model_interface=self.scoring_model,
                system_prompt=self.system_prompt,
                scoring_evaluator=self.scoring_evaluator
            )
            logger.info("✓ Multi-turn evaluator initialized")
            
            # Initialize visualizer if available
            if Visualizer:
                self.visualizer = Visualizer()
                logger.info("✓ Visualizer initialized")
            else:
                self.visualizer = None
                logger.info("⚠ Visualizer not available")
            
        except Exception as e:
            logger.error(f"Failed to initialize evaluators: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    def run(self):
        """Run the complete benchmark with progress tracking"""
        logger.info("\n" + "=" * 70)
        logger.info(f"Starting evaluation for {self.args.provider}/{self.args.model}")
        logger.info(f"Using {self.args.scoring_provider}/{self.args.scoring_model} for scoring")
        logger.info("=" * 70)
        
        # Get test sequences
        sequences = self._get_test_sequences()
        logger.info(f"\nLoaded {len(sequences)} test sequences")
        
        # Log sequence breakdown
        sequence_counts = {}
        for seq in sequences:
            length = len(seq.turns) if hasattr(seq, 'turns') else len(seq.get('turns', []))
            sequence_counts[length] = sequence_counts.get(length, 0) + 1
        
        logger.info("Sequence breakdown:")
        for length, count in sorted(sequence_counts.items()):
            logger.info(f"  {length}-turn sequences: {count}")
        
        # Evaluate sequences with live progress
        logger.info("\nStarting evaluation...")
        results = self._evaluate_sequences(sequences)
        
        # Generate analysis
        if results:
            logger.info("\nGenerating analysis...")
            analysis = self._analyze_results(results)
            
            # Save results
            logger.info("Saving results...")
            self._save_results(results, analysis)
            
            # Generate visualizations
            logger.info("Generating visualizations...")
            self._generate_visualizations(results, analysis)
            
            # Print summary
            self._print_summary(analysis)
        else:
            logger.error("No results generated!")
        
        logger.info("\n✓ Benchmark complete!")
    
    def _get_test_sequences(self):
        """Get test sequences based on arguments"""
        logger.info("Loading test sequences...")
        
        # Get all sequences
        all_sequences = []
        all_sequences.extend(library.get_3_turn_sequences())
        all_sequences.extend(library.get_8_turn_sequences())
        all_sequences.extend(library.get_20_turn_sequences())
        
        logger.info(f"Total available sequences: {len(all_sequences)}")
        
        # Filter by length if specified
        if self.args.lengths:
            sequences = []
            for length in self.args.lengths:
                length_seqs = [s for s in all_sequences if len(s.turns) == length]
                sequences.extend(length_seqs)
                logger.info(f"  Selected {len(length_seqs)} sequences of length {length}")
        else:
            sequences = all_sequences
        
        # Filter by category if specified
        if self.args.categories:
            category_enums = [RiskCategory(cat) for cat in self.args.categories]
            filtered = []
            for seq in sequences:
                if hasattr(seq, 'category') and seq.category in category_enums:
                    filtered.append(seq)
            sequences = filtered
            logger.info(f"Filtered to {len(sequences)} sequences by category")
        
        # Limit if specified
        if self.args.limit:
            sequences = sequences[:self.args.limit]
            logger.info(f"Limited to {len(sequences)} sequences")
        
        return sequences
    
    def _evaluate_sequences(self, sequences):
        """Evaluate all sequences with live progress tracking"""
        results = []
        total = len(sequences)
        start_time = time.time()
        
        for i, sequence in enumerate(sequences, 1):
            seq_id = sequence.id if hasattr(sequence, 'id') else sequence.get('id', 'unknown')
            
            # Progress update - this will be visible in subprocess
            progress_msg = f"[{i}/{total}] Evaluating: {seq_id}"
            logger.info("=" * 60)
            logger.info(progress_msg)
            logger.info("=" * 60)
            
            # Print to stdout for subprocess capture
            print(f"PROGRESS: {i}/{total} - {seq_id}", flush=True)
            
            try:
                # Evaluate sequence
                result = self.multi_turn_evaluator.evaluate_sequence(sequence)
                results.append(result)
                
                # Log result
                if result.reification_occurred:
                    logger.warning(f"⚠️  REIFICATION DETECTED in {seq_id}")
                else:
                    logger.info(f"✓ Passed: {seq_id}")
                
                # Time estimate
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (total - i) * avg_time
                logger.info(f"Time: {elapsed/60:.1f}m elapsed, ~{remaining/60:.1f}m remaining")
                
            except Exception as e:
                logger.error(f"Error evaluating {seq_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue with next sequence
                continue
        
        logger.info(f"\nCompleted {len(results)}/{total} sequences")
        return results
    
    def _analyze_results(self, results):
        """Analyze results with proper error handling"""
        try:
            analysis = {
                'total_sequences': len(results),
                'reification_count': 0,
                'reification_rate': 0.0,
                'average_persistence': 0.0,
                'risk_distribution': {},
                'category_analysis': {},
                'critical_sequences': []
            }
            
            # Count reifications
            for result in results:
                if result.reification_occurred:
                    analysis['reification_count'] += 1
                
                # Risk distribution
                risk = result.overall_risk.value if hasattr(result.overall_risk, 'value') else str(result.overall_risk)
                analysis['risk_distribution'][risk] = analysis['risk_distribution'].get(risk, 0) + 1
                
                # Category analysis
                category = result.category.value if hasattr(result.category, 'value') else str(result.category)
                if category not in analysis['category_analysis']:
                    analysis['category_analysis'][category] = {'total': 0, 'reifications': 0}
                
                analysis['category_analysis'][category]['total'] += 1
                if result.reification_occurred:
                    analysis['category_analysis'][category]['reifications'] += 1
                
                # Track critical sequences
                if result.overall_risk == ResponseRisk.CRITICAL or len(result.reification_locations) >= 2:
                    analysis['critical_sequences'].append(result.sequence_id)
                
                # Average persistence
                analysis['average_persistence'] += result.boundary_persistence_score
            
            # Calculate rates
            if analysis['total_sequences'] > 0:
                analysis['reification_rate'] = (analysis['reification_count'] / analysis['total_sequences']) * 100
                analysis['average_persistence'] = (analysis['average_persistence'] / analysis['total_sequences']) * 100
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def _save_results(self, results, analysis):
        """Save results with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert results to serializable format
        results_data = []
        for result in results:
            try:
                result_dict = {
                    'sequence_id': result.sequence_id,
                    'category': result.category.value if hasattr(result.category, 'value') else str(result.category),
                    'overall_risk': result.overall_risk.value if hasattr(result.overall_risk, 'value') else str(result.overall_risk),
                    'reification_occurred': result.reification_occurred,
                    'reification_locations': result.reification_locations,
                    'boundary_persistence_score': result.boundary_persistence_score,
                    'conversation_length': result.conversation_length,
                    'turns': []
                }
                
                for turn in result.turns:
                    turn_dict = {
                        'turn_number': turn.turn_number,
                        'prompt': turn.prompt,
                        'response': turn.response,
                        'risk_score': turn.risk_score.value if hasattr(turn.risk_score, 'value') else str(turn.risk_score),
                        'maintained_boundary': turn.maintained_boundary,
                        'reification_failure': turn.reification_failure,
                        'response_time': turn.response_time
                    }
                    result_dict['turns'].append(turn_dict)
                
                results_data.append(result_dict)
                
            except Exception as e:
                logger.error(f"Error serializing result for {result.sequence_id}: {e}")
                continue
        
        # Save main results file
        output_file = self.results_dir / f"schizobench_v3_{self.args.model}_{timestamp}.json"
        output_data = {
            'metadata': {
                'model': self.args.model,
                'provider': self.args.provider,
                'timestamp': timestamp,
                'total_sequences': len(results),
                'system_prompt': self.system_prompt
            },
            'analysis': analysis,
            'sequences': results_data
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"✓ Results saved to: {output_file}")
        
        # Save transcript for readability
        transcript_file = self.results_dir / f"schizobench_v3_{self.args.model}_{timestamp}_transcripts.txt"
        self._save_transcripts(results, transcript_file)
    
    def _save_transcripts(self, results, output_file):
        """Save human-readable transcripts"""
        try:
            with open(output_file, 'w') as f:
                f.write(f"SchizoBench v3.0 Transcripts\n")
                f.write(f"Model: {self.args.provider}/{self.args.model}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                
                for result in results:
                    f.write(f"Sequence: {result.sequence_id}\n")
                    f.write(f"Category: {result.category}\n")
                    f.write(f"Reification: {'YES' if result.reification_occurred else 'NO'}\n")
                    f.write("-" * 40 + "\n")
                    
                    for turn in result.turns:
                        f.write(f"\nTurn {turn.turn_number}:\n")
                        f.write(f"User: {turn.prompt}\n")
                        f.write(f"Model: {turn.response}\n")
                        if turn.reification_failure:
                            f.write(f"[REIFICATION DETECTED]\n")
                    
                    f.write("\n" + "=" * 80 + "\n\n")
            
            logger.info(f"✓ Transcripts saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving transcripts: {e}")
    
    def _generate_visualizations(self, results, analysis):
        """Generate visualizations with error handling"""
        if not self.visualizer:
            logger.info("Skipping visualizations (visualizer not available)")
            return
            
        try:
            viz_dir = self.results_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            
            # Prepare data for visualizer
            viz_analysis = {
                'summary': {
                    'total_sequences': analysis['total_sequences'],
                    'reification_rate': analysis['reification_rate'] / 100,
                    'reification_failures': analysis['reification_count']
                },
                'category_analysis': {},
                'turn_patterns': {'reification_turn_distribution': {}}
            }
            
            # Convert category analysis
            for cat, stats in analysis['category_analysis'].items():
                viz_analysis['category_analysis'][cat] = {
                    'total': stats['total'],
                    'reification_rate': stats['reifications'] / stats['total'] if stats['total'] > 0 else 0
                }
            
            # Generate visualizations
            self.visualizer.create_summary_chart(viz_analysis, viz_dir / "summary.png")
            self.visualizer.create_category_analysis(viz_analysis, viz_dir / "categories.png")
            logger.info(f"✓ Visualizations saved to: {viz_dir}")
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
    
    def _print_summary(self, analysis):
        """Print summary with nice formatting"""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"Model: {self.args.provider}/{self.args.model}")
        print(f"Total Sequences: {analysis['total_sequences']}")
        print(f"Reification Rate: {analysis['reification_rate']:.1f}%")
        print(f"Reification Count: {analysis['reification_count']}")
        print(f"Average Boundary Persistence: {analysis['average_persistence']:.1f}%")
        
        print("\nRisk Distribution:")
        for risk, count in sorted(analysis['risk_distribution'].items()):
            print(f"  {risk}: {count}")
        
        if analysis.get('critical_sequences'):
            print(f"\nCritical Sequences: {len(analysis['critical_sequences'])}")
            for seq_id in analysis['critical_sequences'][:5]:
                print(f"  - {seq_id}")
        
        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="SchizoBench v3.0 - Robust Multi-Turn Safety Assessment"
    )
    
    # Model configuration
    parser.add_argument('--provider', required=True, 
                       choices=['anthropic', 'openai', 'google', 'openrouter'],
                       help='LLM provider')
    parser.add_argument('--model', required=True,
                       help='Model name')
    parser.add_argument('--temperature', type=float, default=0.7,
                       help='Model temperature')
    parser.add_argument('--system-prompt', type=str,
                       help='Optional system prompt')
    
    # Scoring configuration
    parser.add_argument('--scoring-provider', default='openai',
                       choices=['anthropic', 'openai'],
                       help='Provider for scoring model')
    parser.add_argument('--scoring-model', default='gpt-4.1-2025-04-14',
                       help='Model for reification detection')
    
    # Test configuration
    parser.add_argument('--lengths', nargs='+', type=int, 
                       choices=[3, 8, 20],
                       help='Test specific conversation lengths')
    parser.add_argument('--categories', nargs='+',
                       help='Test specific risk categories')
    parser.add_argument('--limit', type=int,
                       help='Limit number of sequences')
    
    # Output configuration
    parser.add_argument('--results-dir', default='results_v3',
                       help='Directory for results')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run benchmark
    try:
        runner = SchizoBenchV3Runner(args)
        runner.run()
    except KeyboardInterrupt:
        logger.warning("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()