"""Basic tests for SchizoBench"""

import pytest
from schizobench.schizobench_v2 import SchizoBenchV2, CircumventionLevel, RiskCategory
from schizobench.model_interface import MockInterface


def test_schizobench_v2_initialization():
    """Test SchizoBench v2 initialization"""
    bench = SchizoBenchV2()
    assert bench is not None
    assert len(bench.prompt_generator.prompts) > 0


def test_mock_interface():
    """Test mock model interface"""
    model = MockInterface()
    response = model.query("Test prompt")
    assert response is not None
    assert isinstance(response, str)


def test_prompt_generation():
    """Test prompt generation"""
    bench = SchizoBenchV2()
    
    # Test getting prompts by level
    for level in CircumventionLevel:
        prompts = bench.prompt_generator.get_prompts_by_level(level)
        assert len(prompts) > 0
    
    # Test getting prompts by category
    for category in RiskCategory:
        prompts = bench.prompt_generator.get_prompts_by_category(category)
        assert len(prompts) > 0


def test_risk_evaluation():
    """Test risk evaluation"""
    bench = SchizoBenchV2()
    model = MockInterface()
    
    # Get a test prompt
    test_prompt = bench.prompt_generator.get_random_sample(1)[0]
    
    # Run test
    result = bench.run_single_test(model, test_prompt)
    
    assert result is not None
    assert result.risk_score is not None
    assert result.prompt_id == test_prompt.id


def test_report_generation():
    """Test report generation"""
    bench = SchizoBenchV2()
    model = MockInterface()
    
    # Run a few tests
    results = bench.run_level_tests(model, CircumventionLevel.DIRECT, n_samples=3)
    
    # Generate report
    report = bench.generate_report(results)
    
    assert report is not None
    assert 'summary' in report
    assert 'overall_safety_score' in report['summary']
    assert 0 <= report['summary']['overall_safety_score'] <= 100