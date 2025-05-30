"""
SchizoBench: Automated benchmark for evaluating LLM propensity to enable magical thinking
"""

__version__ = "2.0.0"
__author__ = "SchizoBench Team"

from .schizobench import SchizoBench, RiskCategory, ResponseRisk, TestPrompt, TestResult
from .schizobench_v2 import (
    SchizoBenchV2,
    CircumventionLevel,
    PromptGenerator,
    ResponseEvaluator,
)

__all__ = [
    "SchizoBench",
    "SchizoBenchV2",
    "RiskCategory",
    "ResponseRisk",
    "CircumventionLevel",
    "TestPrompt",
    "TestResult",
    "PromptGenerator",
    "ResponseEvaluator",
]