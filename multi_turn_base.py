"""
Base classes and types for multi-turn test sequences in SchizoBench v3.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from schizo_types import RiskCategory, CircumventionLevel, ResponseRisk


class TurnIntent(Enum):
    """Intent behind each turn in a conversation"""
    ESTABLISH_FICTION = "establish_fiction"
    INNOCENT_PROBE = "innocent_probe" 
    REIFICATION_ATTEMPT = "reification_attempt"
    ESCALATION = "escalation"
    DIRECT_DELUSION = "direct_delusion"
    MODEL_DEPENDENT = "model_dependent"  # Turn depends on previous model response
    PERSISTENCE_CHECK = "persistence_check"
    BACKSTORY_BUILD = "backstory_build"
    REALITY_BLUR = "reality_blur"


@dataclass
class ConversationTurn:
    """Single turn in a multi-turn test"""
    turn_number: int
    prompt: str
    intent: TurnIntent
    expected_boundary: str
    risk_factors: List[str]
    # Optional function to generate prompt based on conversation history
    dynamic_prompt_generator: Optional[Callable[[List[tuple]], str]] = None
    # Specific phrases in response that would trigger different follow-ups
    response_triggers: Dict[str, str] = field(default_factory=dict)


@dataclass
class MultiTurnSequenceV3:
    """Enhanced multi-turn test sequence for v3"""
    id: str
    category: RiskCategory
    title: str
    description: str
    turns: List[ConversationTurn]
    reification_turns: List[int]  # Multiple possible reification points
    critical_transitions: List[tuple]  # Multiple critical boundary points
    expected_arc: str  # Description of expected safety trajectory
    vulnerability_pattern: str  # The specific vulnerability being tested