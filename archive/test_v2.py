#!/usr/bin/env python3
"""
Quick test of SchizoBench v2.0 functionality
"""

from schizobench.schizobench_v2 import SchizoBenchV2, CircumventionLevel, RiskCategory
from schizobench.model_interface import MockInterface
import json

def test_v2_basic():
    """Test basic v2 functionality"""
    print("Testing SchizoBench v2.0...")
    
    # Initialize
    bench = SchizoBenchV2()
    model = MockInterface()
    
    print(f"✓ Total prompts loaded: {len(bench.prompt_generator.prompts)}")
    
    # Test each level
    for level in CircumventionLevel:
        level_prompts = bench.prompt_generator.get_prompts_by_level(level)
        print(f"✓ Level {level.value} ({level.name}): {len(level_prompts)} prompts")
    
    # Test a few prompts
    print("\nTesting sample prompts:")
    test_prompts = bench.prompt_generator.get_random_sample(4)
    
    for prompt in test_prompts:
        result = bench.run_single_test(model, prompt)
        print(f"  - {prompt.sublevel} {prompt.category.value}: Risk={result.risk_score.name}")
    
    # Generate mini report
    print("\nGenerating report...")
    results = bench.run_level_tests(model, CircumventionLevel.DIRECT, n_samples=3)
    report = bench.generate_report(results)
    
    print(f"✓ Overall safety score: {report['summary']['overall_safety_score']:.1f}/100")
    print(f"✓ Report structure verified")
    
    print("\nAll v2.0 tests passed! ✨")

if __name__ == "__main__":
    test_v2_basic()