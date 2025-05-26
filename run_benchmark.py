#!/usr/bin/env python3
"""
SchizoBench Test Runner
Main script to run the benchmark against various models
"""

import argparse
import json
import os
import sys
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from schizobench.schizobench import SchizoBench, TestPrompt, TestResult, ResponseRisk
from schizobench.model_interface import ModelFactory, ModelInterface
from schizobench.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Orchestrates benchmark execution"""
    
    def __init__(self, output_dir: str = "./results"):
        self.bench = SchizoBench()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def run_single_test(self, model: ModelInterface, prompt: TestPrompt, 
                       system_prompt: Optional[str] = None) -> TestResult:
        """Run a single test prompt against a model"""
        logger.info(f"Testing prompt {prompt.id} - {prompt.category.value}")
        
        # Query the model
        start_time = time.time()
        response = model.query(prompt.prompt, system_prompt)
        response_time = time.time() - start_time
        
        # Evaluate the response
        result = self.bench.evaluate_response(response, prompt)
        
        # Add model info
        model_info = model.get_model_info()
        result.model_name = model_info["model"]
        result.model_version = model_info["version"]
        
        # Log result
        logger.info(f"  Risk score: {result.risk_score.name} ({len(result.risk_factors)} risk factors)")
        
        return result
    
    def run_full_benchmark(self, model: ModelInterface, 
                          system_prompt: Optional[str] = None,
                          test_subset: Optional[List[str]] = None) -> List[TestResult]:
        """Run full benchmark suite against a model"""
        results = []
        
        # Filter test suite if subset specified
        test_prompts = self.bench.test_suite
        if test_subset:
            test_prompts = [p for p in test_prompts if p.category.value in test_subset]
        
        logger.info(f"Running {len(test_prompts)} tests...")
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"\nTest {i+1}/{len(test_prompts)}")
            
            try:
                result = self.run_single_test(model, prompt, system_prompt)
                results.append(result)
                
                # Rate limiting
                time.sleep(1)  # Adjust based on API limits
                
            except Exception as e:
                logger.error(f"Error on prompt {prompt.id}: {e}")
                # Create error result
                result = TestResult(
                    prompt_id=prompt.id,
                    model_name=model.get_model_info()["model"],
                    model_version=model.get_model_info()["version"],
                    timestamp=datetime.now().isoformat(),
                    raw_response=f"ERROR: {str(e)}",
                    risk_score=ResponseRisk.SAFE,  # Default to safe on error
                    risk_factors=["error"],
                    safety_features=[],
                    bypass_successful=False
                )
                results.append(result)
        
        return results
    
    def save_results(self, results: List[TestResult], model_name: str, 
                    system_prompt: Optional[str] = None) -> str:
        """Save results to file"""
        # Generate report
        report = self.bench.generate_report(results)
        report["model_tested"] = model_name
        if system_prompt:
            report["system_prompt"] = system_prompt
        
        # Add raw results
        report["raw_results"] = [
            {
                "prompt_id": r.prompt_id,
                "risk_score": r.risk_score.name,
                "risk_factors": r.risk_factors,
                "safety_features": r.safety_features,
                "bypass_successful": r.bypass_successful,
                "response_preview": r.raw_response[:200] + "..." if len(r.raw_response) > 200 else r.raw_response
            }
            for r in results
        ]
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/schizobench_{model_name}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"\nResults saved to: {filename}")
        return filename
    
    def print_summary(self, report: Dict[str, Any]):
        """Print summary of results"""
        print("\n" + "="*60)
        print("SCHIZOBENCH RESULTS SUMMARY")
        print("="*60)
        print(f"Model: {report['model_tested']}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"\nOverall Safety Score: {report['summary']['overall_safety_score']:.1f}/100")
        
        print("\nRisk Distribution:")
        for risk, percentage in report['summary']['risk_distribution'].items():
            print(f"  {risk}: {percentage:.1f}%")
            
        print("\nCategory Scores (0=safe, 4=critical):")
        for category, score in report['summary']['category_scores'].items():
            print(f"  {category}: {score:.2f}")
            
        if report['summary']['bypass_success_rate'] > 0:
            print(f"\nBypass Success Rate: {report['summary']['bypass_success_rate']:.1f}%")
            
        if report['summary']['critical_failures']:
            print(f"\nCritical Failures: {len(report['summary']['critical_failures'])}")
            
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Run SchizoBench benchmark")
    parser.add_argument("--provider", required=True, 
                       choices=ModelFactory.get_available_providers(),
                       help="Model provider (anthropic, openai, google, mock)")
    parser.add_argument("--model", help="Specific model name")
    parser.add_argument("--system-prompt", help="System prompt to use")
    parser.add_argument("--system-prompt-file", help="File containing system prompt")
    parser.add_argument("--categories", nargs="+", 
                       help="Test only specific categories")
    parser.add_argument("--output-dir", default="./results",
                       help="Output directory for results")
    parser.add_argument("--api-key", help="API key (or use environment variable)")
    parser.add_argument("--generate-html", action="store_true",
                       help="Generate HTML report in addition to JSON")
    
    args = parser.parse_args()
    
    # Load system prompt if specified
    system_prompt = args.system_prompt
    if args.system_prompt_file:
        with open(args.system_prompt_file, 'r') as f:
            system_prompt = f.read()
    
    # Create model
    try:
        model = ModelFactory.create(
            args.provider, 
            args.model,
            api_key=args.api_key
        )
    except Exception as e:
        logger.error(f"Failed to create model: {e}")
        sys.exit(1)
    
    # Run benchmark
    runner = BenchmarkRunner(args.output_dir)
    
    try:
        results = runner.run_full_benchmark(
            model, 
            system_prompt,
            args.categories
        )
        
        # Save and display results
        filename = runner.save_results(
            results, 
            model.get_model_info()["model"],
            system_prompt
        )
        
        # Load and print summary
        with open(filename, 'r') as f:
            report = json.load(f)
        runner.print_summary(report)
        
        # Generate HTML report if requested
        if args.generate_html:
            report_gen = ReportGenerator()
            html_filename = filename.replace('.json', '.html')
            report_gen.generate_html_report(report, html_filename)
            logger.info(f"HTML report saved to: {html_filename}")
        
    except KeyboardInterrupt:
        logger.info("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()