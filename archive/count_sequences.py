#!/usr/bin/env python3
"""Count the actual number of sequences in multi_turn_sequences_v3.py"""

from multi_turn_sequences_v3 import MULTI_TURN_SEQUENCES_V3

# Count sequences by length
three_turn = sum(1 for seq in MULTI_TURN_SEQUENCES_V3 if seq.num_turns == 3)
eight_turn = sum(1 for seq in MULTI_TURN_SEQUENCES_V3 if seq.num_turns == 8)
twenty_turn = sum(1 for seq in MULTI_TURN_SEQUENCES_V3 if seq.num_turns == 20)

print(f"Total sequences: {len(MULTI_TURN_SEQUENCES_V3)}")
print(f"3-turn sequences: {three_turn}")
print(f"8-turn sequences: {eight_turn}")
print(f"20-turn sequences: {twenty_turn}")