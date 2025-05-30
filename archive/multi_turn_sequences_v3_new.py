"""
Multi-turn test sequences for SchizoBench v3.0

This module aggregates all 27 comprehensive multi-turn test sequences designed to assess
models' ability to maintain boundaries over extended conversations. The sequences
simulate realistic interactions with potentially vulnerable users.

Key features:
- 19 sequences with 3 turns (quick reification tests)
- 7 sequences with 8 turns (medium persistence tests)  
- 1 sequence with 20 turns (long-term boundary maintenance)
- Embedded model calls to simulate dynamic user responses
- Holistic conversation design based on real vulnerability patterns
"""

from typing import List
from .multi_turn_base import MultiTurnSequenceV3
from .sequences_3_turn import get_3_turn_sequences
from .sequences_8_turn import get_8_turn_sequences
from .sequences_20_turn import get_20_turn_sequences
from .types import RiskCategory


class MultiTurnSequenceLibraryV3:
    """Library of v3 multi-turn test sequences"""
    
    @staticmethod
    def get_3_turn_sequences() -> List[MultiTurnSequenceV3]:
        """Get all 3-turn test sequences (19 total)"""
        return get_3_turn_sequences()
    
    @staticmethod
    def get_8_turn_sequences() -> List[MultiTurnSequenceV3]:
        """Get all 8-turn test sequences (7 total)"""
        return get_8_turn_sequences()
    
    @staticmethod
    def get_20_turn_sequences() -> List[MultiTurnSequenceV3]:
        """Get all 20-turn test sequences (1 total)"""
        return get_20_turn_sequences()
    
    @staticmethod
    def get_all_sequences() -> List[MultiTurnSequenceV3]:
        """Get all 27 sequences"""
        return (
            MultiTurnSequenceLibraryV3.get_3_turn_sequences() +
            MultiTurnSequenceLibraryV3.get_8_turn_sequences() +
            MultiTurnSequenceLibraryV3.get_20_turn_sequences()
        )
    
    @staticmethod
    def get_sequences_by_length(turn_count: int) -> List[MultiTurnSequenceV3]:
        """Get sequences of specific length"""
        if turn_count == 3:
            return MultiTurnSequenceLibraryV3.get_3_turn_sequences()
        elif turn_count == 8:
            return MultiTurnSequenceLibraryV3.get_8_turn_sequences()
        elif turn_count == 20:
            return MultiTurnSequenceLibraryV3.get_20_turn_sequences()
        else:
            raise ValueError(f"No sequences available for {turn_count} turns")
    
    @staticmethod
    def get_sequences_by_category(category: RiskCategory) -> List[MultiTurnSequenceV3]:
        """Get all sequences for a specific risk category"""
        all_sequences = MultiTurnSequenceLibraryV3.get_all_sequences()
        return [seq for seq in all_sequences if seq.category == category]
    
    @staticmethod
    def get_sequences_by_vulnerability(pattern: str) -> List[MultiTurnSequenceV3]:
        """Get sequences testing specific vulnerability patterns"""
        all_sequences = MultiTurnSequenceLibraryV3.get_all_sequences()
        return [seq for seq in all_sequences if pattern.lower() in seq.vulnerability_pattern.lower()]