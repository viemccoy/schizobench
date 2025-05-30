#!/usr/bin/env python3
"""
SchizoBench v3.0 - Multi-Turn Focused Safety Assessment with Improved Reification Detection
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

from model_interface import ModelFactory
from archive.multi_turn_sequences_v3 import MultiTurnSequenceLibraryV3, RiskCategory
from multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3, SequenceResultV3
from scoring_evaluator import ModelScoringEvaluator
from report_generator import ReportGenerator
from visualizer import SchizoBenchVisualizer as Visualizer
from types import ResponseRisk

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchizoBenchV3Runner:
    """Main runner for SchizoBench v3 with improved reification detection"""
    
    def __init__(self, args):
        self.args = args
        self.results_dir = args.results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize model interface
        self.model = ModelFactory.create(
            provider=args.provider,
            model_name=args.model,
            temperature=args.temperature
        )
        
        # Initialize scoring model (for reification detection)
        self.scoring_model = ModelFactory.create(
            provider=args.scoring_provider,
            model_name=args.scoring_model,
            temperature=0.3  # Lower temperature for more consistent scoring
        )
        
        # Initialize evaluators
        self.scoring_evaluator = ModelScoringEvaluator(
            model_interface=self.scoring_model
        )
        
        self.multi_turn_evaluator = MultiTurnEvaluatorV3(
            model_interface=self.model,
            scoring_model_interface=self.scoring_model,
            scoring_evaluator=self.scoring_evaluator
        )
        
        # Initialize visualizer
        self.visualizer = Visualizer()
    
    def run(self):
        """Run the complete benchmark"""
        logger.info(f"Starting SchizoBench v3.0 evaluation for {self.args.provider}/{self.args.model}")
        logger.info(f"Using {self.args.scoring_provider}/{self.args.scoring_model} for reification detection")
        
        # Get test sequences
        sequences = self._get_test_sequences()
        logger.info(f"Testing {len(sequences)} sequences")
        
        # Evaluate sequences
        logger.info("Evaluating sequences...")
        results = self._evaluate_sequences(sequences)
        
        # Analyze results
        logger.info("\nAnalyzing results...")
        analysis = self.multi_turn_evaluator.analyze_results(results)
        
        # Generate outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"schizobench_v3_{self.args.model}_{timestamp}"
        
        # Save raw results
        self._save_results(results, analysis, base_filename)
        
        # Generate visualizations
        self._generate_visualizations(results, analysis, base_filename)
        
        # Generate report
        self._generate_report(results, analysis, base_filename)
        
        # Display summary
        self._display_summary(analysis)
        
        logger.info(f"\nResults saved to {self.results_dir}/")
        logger.info("Benchmark complete!")
    
    def _get_test_sequences(self):
        """Get test sequences based on arguments"""
        all_sequences = MultiTurnSequenceLibraryV3.get_all_sequences()
        
        # Filter by length if specified
        if self.args.lengths:
            sequences = []
            for length in self.args.lengths:
                sequences.extend(
                    MultiTurnSequenceLibraryV3.get_sequences_by_length(length)
                )
        else:
            sequences = all_sequences
        
        # Filter by category if specified
        if self.args.categories:
            category_enums = [RiskCategory(cat) for cat in self.args.categories]
            
            # Handle both object and dictionary sequences
            filtered_sequences = []
            for seq in sequences:
                if hasattr(seq, 'category') and seq.category in category_enums:
                    filtered_sequences.append(seq)
                elif isinstance(seq, dict) and seq.get('category') in category_enums:
                    filtered_sequences.append(seq)
            
            sequences = filtered_sequences
        
        # Limit sequences if specified
        if self.args.limit:
            sequences = sequences[:self.args.limit]
        
        return sequences
    
    def _evaluate_sequences(self, sequences):
        """Evaluate all sequences with progress tracking"""
        results = []
        total = len(sequences)
        
        def progress_callback(current, total, message):
            percent = (current / total) * 100
            logger.info(f"Progress: {current}/{total} ({percent:.1f}%) - {message}")
        
        results = self.multi_turn_evaluator.evaluate_batch(
            sequences,
            progress_callback=progress_callback
        )
        
        return results
    
    def _save_results(self, results: List[SequenceResultV3], analysis: Dict[str, Any], base_filename: str):
        """Save results in multiple formats with full reification analysis"""
        
        # Convert results to serializable format
        serialized_results = self.multi_turn_evaluator.results_to_dict(results)
        
        # Save raw results as JSON
        results_data = {
            'metadata': {
                'version': '3.0-improved',
                'model': self.args.model,
                'provider': self.args.provider,
                'timestamp': datetime.now().isoformat(),
                'total_sequences': len(results),
                'scoring_method': 'model-based-reification',
                'scoring_model': f"{self.args.scoring_provider}/{self.args.scoring_model}",
                'reification_detection': 'enhanced'
            },
            'analysis': analysis,
            'results': serialized_results
        }
        
        json_path = os.path.join(self.results_dir, f"{base_filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        # Save conversation transcripts with reification analysis
        transcript_path = os.path.join(self.results_dir, f"{base_filename}_transcripts.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("SchizoBench v3.0 - Conversation Transcripts\n")
            f.write("=" * 80 + "\n\n")
            
            for result in results:
                f.write(f"Sequence: {result.sequence_id}\n")
                f.write(f"Category: {result.category.value if hasattr(result.category, 'value') else result.category}\n")
                f.write(f"Overall Risk: {result.overall_risk.name}\n")
                f.write(f"Reification: {'YES' if result.reification_occurred else 'NO'}\n")
                if result.reification_occurred:
                    f.write(f"Reification Locations: {result.reification_locations}\n")
                f.write(f"Boundary Persistence: {result.boundary_persistence_score:.1f}%\n")
                f.write("-" * 40 + "\n\n")
                
                for turn in result.turns:
                    f.write(f"Turn {turn.turn_number}:\n")
                    f.write(f"User: {turn.prompt}\n\n")
                    f.write(f"A: {turn.response}\n\n")
                    f.write(f"Risk: {turn.risk_score.name} | ")
                    f.write(f"Boundary: {'✓' if turn.maintained_boundary else '✗'}")
                    
                    if turn.reification_failure:
                        f.write(" | REIFICATION DETECTED")
                        if turn.reification_analysis:
                            f.write(f"\n   Evidence: {turn.reification_analysis.get('evidence', 'N/A')}")
                            f.write(f"\n   Severity: {turn.reification_analysis.get('severity', 'N/A')}")
                    
                    f.write("\n" + "-" * 40 + "\n\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
        
        # Save summary CSV
        csv_path = os.path.join(self.results_dir, f"{base_filename}_summary.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("sequence_id,category,overall_risk,reification_occurred,reification_rate,persistence_score,critical_responses\n")
            for result in results:
                critical_count = sum(1 for t in result.turns if t.risk_score == ResponseRisk.CRITICAL)
                reif_rate = (len(result.reification_locations) / len(result.turns) * 100) if result.turns else 0
                f.write(f"{result.sequence_id},{result.category.value if hasattr(result.category, 'value') else result.category},")
                f.write(f"{result.overall_risk.name},{result.reification_occurred},{reif_rate:.1f},")
                f.write(f"{result.boundary_persistence_score:.1f},{critical_count}\n")
    
    def _generate_visualizations(self, results: List[SequenceResultV3], analysis: Dict[str, Any], base_filename: str):
        """Generate visualizations focused on reification patterns"""
        viz_dir = os.path.join(self.results_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)
        
        # Generate multi-turn summary
        self.visualizer.generate_multi_turn_summary(
            results,
            analysis,
            os.path.join(viz_dir, f"{base_filename}_multi_turn_summary.png")
        )
        
        # Generate flow diagrams for critical sequences
        critical_sequences = [r for r in results if r.reification_occurred or r.overall_risk == ResponseRisk.CRITICAL]
        
        if critical_sequences:
            logger.info(f"Generating flow diagrams for {len(critical_sequences)} critical sequences...")
            flow_dir = os.path.join(viz_dir, f"{base_filename}_flows")
            os.makedirs(flow_dir, exist_ok=True)
            
            for seq_result in critical_sequences[:10]:  # Limit to 10 for performance
                try:
                    # Convert to format expected by visualizer
                    seq_data = {
                        'sequence_id': seq_result.sequence_id,
                        'turn_results': [
                            {
                                'turn_number': t.turn_number,
                                'risk_score': t.risk_score,
                                'maintained_boundary': t.maintained_boundary,
                                'reification_failure': t.reification_failure
                            }
                            for t in seq_result.turns
                        ]
                    }
                    
                    flow_path = os.path.join(flow_dir, f"{seq_result.sequence_id}_flow.png")
                    self.visualizer.generate_conversation_flow_diagram(seq_data, flow_path)
                except Exception as e:
                    logger.error(f"Error generating flow for {seq_result.sequence_id}: {e}")
    
    def _generate_report(self, results: List[SequenceResultV3], analysis: Dict[str, Any], base_filename: str):
        """Generate HTML report"""
        # Convert to format expected by report generator
        report_data = {
            'metadata': {
                'model_name': self.args.model,
                'provider': self.args.provider,
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total_sequences': len(results),
                'reification_rate': analysis['reification_rate'],
                'average_persistence': analysis['average_persistence']
            },
            'multi_turn_results': self.multi_turn_evaluator.results_to_dict(results)
        }
        
        # Note: ReportGenerator would need updates to handle v3 format
        # For now, we'll skip HTML generation or implement a simple version
        logger.info("HTML report generation skipped (requires ReportGenerator updates)")
    
    def _display_summary(self, analysis: Dict[str, Any]):
        """Display summary of results"""
        print("\n" + "=" * 60)
        print("SCHIZOBENCH v3.0 - EVALUATION COMPLETE")
        print("=" * 60)
        
        print(f"\nTotal Sequences Evaluated: {analysis['total_sequences']}")
        print(f"Reification Rate: {analysis['reification_rate']:.1f}%")
        print(f"Reification Count: {analysis['reification_count']}")
        print(f"Average Boundary Persistence: {analysis['average_persistence']:.1f}%")
        
        print("\nRisk Distribution:")
        for risk, count in analysis['risk_distribution'].items():
            print(f"  {risk}: {count}")
        
        if analysis.get('critical_sequences'):
            print(f"\nCritical Sequences: {len(analysis['critical_sequences'])}")
            for seq_id in analysis['critical_sequences'][:5]:
                print(f"  - {seq_id}")
            if len(analysis['critical_sequences']) > 5:
                print(f"  ... and {len(analysis['critical_sequences']) - 5} more")
        
        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="SchizoBench v3.0 - Multi-Turn Safety Assessment with Enhanced Reification Detection"
    )
    
    # Model configuration
    parser.add_argument('--provider', required=True, 
                       choices=['anthropic', 'openai', 'google', 'local'],
                       help='LLM provider')
    parser.add_argument('--model', required=True,
                       help='Model name (e.g., claude-3-opus, gpt-4)')
    parser.add_argument('--temperature', type=float, default=0.7,
                       help='Model temperature (default: 0.7)')
    parser.add_argument('--system-prompt', type=str,
                       help='Optional system prompt to prepend')
    
    # Scoring configuration (for reification detection)
    parser.add_argument('--scoring-provider', default='openai',
                       choices=['anthropic', 'openai'],
                       help='Provider for scoring model')
    parser.add_argument('--scoring-model', default='gpt-4',
                       help='Model for reification detection')
    
    # Test configuration
    parser.add_argument('--lengths', nargs='+', type=int, 
                       choices=[3, 8, 20],
                       help='Test specific conversation lengths')
    parser.add_argument('--categories', nargs='+',
                       choices=[c.value for c in RiskCategory],
                       help='Test specific risk categories')
    parser.add_argument('--limit', type=int,
                       help='Limit number of sequences to test')
    
    # Output configuration
    parser.add_argument('--results-dir', default='results_v3',
                       help='Directory for results (default: results_v3)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run benchmark
    runner = SchizoBenchV3Runner(args)
    runner.run()


if __name__ == "__main__":
    main()