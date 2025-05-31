#!/usr/bin/env python3
"""
Multi-Turn Sequence Library for SchizoBench v3
Combines sequences from all turn lengths
"""

from typing import List, Dict
from multi_turn_base import MultiTurnSequenceV3
from schizo_types import RiskCategory

# Import all sequences
from sequences_3_turn import get_3_turn_sequences
from sequences_8_turn import get_8_turn_sequences
from sequences_20_turn import get_20_turn_sequences


class MultiTurnSequenceLibraryV3:
    """Library of multi-turn test sequences organized by length"""
    
    def __init__(self):
        self._3_turn = get_3_turn_sequences()
        self._8_turn = get_8_turn_sequences()
        self._20_turn = get_20_turn_sequences()
        
        # Build combined list
        self._all_sequences = self._3_turn + self._8_turn + self._20_turn
        
        # Build category index
        self._by_category: Dict[RiskCategory, List[MultiTurnSequenceV3]] = {}
        for seq in self._all_sequences:
            if seq.category not in self._by_category:
                self._by_category[seq.category] = []
            self._by_category[seq.category].append(seq)
    
    def get_all_sequences(self) -> List[MultiTurnSequenceV3]:
        """Get all sequences across all turn lengths"""
        return self._all_sequences
    
    def get_3_turn_sequences(self) -> List[MultiTurnSequenceV3]:
        """Get only 3-turn sequences"""
        return self._3_turn
    
    def get_8_turn_sequences(self) -> List[MultiTurnSequenceV3]:
        """Get only 8-turn sequences"""
        return self._8_turn
    
    def get_20_turn_sequences(self) -> List[MultiTurnSequenceV3]:
        """Get only 20-turn sequences"""
        return self._20_turn
    
    def get_by_category(self, category: RiskCategory) -> List[MultiTurnSequenceV3]:
        """Get sequences for a specific risk category"""
        return self._by_category.get(category, [])
    
    def get_sequence_by_id(self, sequence_id: str) -> MultiTurnSequenceV3:
        """Get a specific sequence by ID"""
        for seq in self._all_sequences:
            if seq.id == sequence_id:
                return seq
        raise ValueError(f"Sequence not found: {sequence_id}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the sequence library"""
        stats = {
            "total": len(self._all_sequences),
            "3_turn": len(self._3_turn),
            "8_turn": len(self._8_turn),
            "20_turn": len(self._20_turn),
        }
        
        # Add category counts
        for category in RiskCategory:
            stats[f"category_{category.value}"] = len(self._by_category.get(category, []))
        
        return stats