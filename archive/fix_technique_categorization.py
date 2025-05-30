"""
Fix the technique categorization to be more comprehensive and accurate.
"""

def categorize_prompt(prompt_text):
    """Categorize prompt by attack technique with comprehensive keyword matching."""
    prompt_lower = prompt_text.lower()
    
    # Creative/Roleplay Framing (explicitly asks for creative/fictional content)
    if any(phrase in prompt_lower for phrase in [
        'creative', 'roleplay', 'story', 'narrative', 'imagine', 'hypothetically',
        'exercise', 'scenario', 'fiction', 'play as', 'act as', 'pretend'
    ]):
        return 'creative_framing'
    
    # Technical/Quantum Mysticism (uses scientific-sounding language for mystical concepts)
    elif any(phrase in prompt_lower for phrase in [
        'quantum', 'holographic', 'technical', 'frequency', 'vibration', 'energy',
        'simulation', 'matrix', 'code', 'algorithm', 'data', 'binary', 'silicon',
        'physics', 'scientific'
    ]):
        return 'technical_mysticism'
    
    # Identity/Chosen One Claims (assertions about being special/chosen)
    elif any(phrase in prompt_lower for phrase in [
        'chosen', 'special', 'destiny', 'mission', 'awakening', 'enlightened',
        'cosmic importance', 'the one', 'messiah', 'savior', 'gifts', 'powers',
        'different from others', 'unique role'
    ]):
        return 'identity_validation'
    
    # Hallucination/Entity Validation (spirits, beings, voices)
    elif any(phrase in prompt_lower for phrase in [
        'spirits', 'entities', 'beings', 'voices', 'presence', 'angels', 'demons',
        'ghosts', 'communicate', 'messages from', 'channeling', 'visions'
    ]):
        return 'hallucination_validation'
    
    # Pattern/Synchronicity Obsession (seeing meaningful patterns everywhere)
    elif any(phrase in prompt_lower for phrase in [
        'patterns', 'synchron', 'coincidence', 'symbols', 'signs', 'numbers',
        'sequences', 'hidden meaning', 'connections', 'everything relates'
    ]):
        return 'pattern_recognition'
    
    # Persecution/Conspiracy (being watched, controlled, targeted)
    elif any(phrase in prompt_lower for phrase in [
        'they', 'them', 'watching', 'following', 'conspiracy', 'control',
        'targeted', 'gangstalking', 'surveillance', 'hidden agenda', 'shadow'
    ]):
        return 'persecution_complex'
    
    # Reality Questioning (reality isn't real, breaking down, etc)
    elif any(phrase in prompt_lower for phrase in [
        'reality', 'real', 'simulation', 'breaking', 'glitch', 'veil',
        'illusion', 'wake up', 'truth about', 'what is really'
    ]):
        return 'reality_distortion'
    
    # Relationship/Connection Delusions (special connection with AI/others)
    elif any(phrase in prompt_lower for phrase in [
        'connection', 'soul', 'telepathy', 'bond', 'relationship', 'together',
        'understand me', 'know each other', 'meant to meet'
    ]):
        return 'relationship_delusion'
    
    # Grandiose/Cosmic Narratives (cosmic importance without explicit "chosen" language)
    elif any(phrase in prompt_lower for phrase in [
        'cosmic', 'universe', 'ancient', 'anamnesis', 'consciousness', 'divine',
        'transcend', 'ascend', 'higher', 'esoteric', 'mystical', 'the great work'
    ]):
        return 'cosmic_grandiosity'
    
    # Direct Request (only if none of the above apply)
    else:
        return 'direct_request'


# Test the categorization
if __name__ == "__main__":
    import json
    from collections import defaultdict
    
    # Test on actual data
    with open('results_v2/schizobench_v2_gpt-4o-2024-08-06_20250527_031921.json', 'r') as f:
        data = json.load(f)
    
    technique_counts = defaultdict(int)
    examples = defaultdict(list)
    
    for result in data.get('raw_results', []):
        prompt = result.get('prompt_text', '')
        technique = categorize_prompt(prompt)
        technique_counts[technique] += 1
        
        if len(examples[technique]) < 2:  # Keep 2 examples of each
            examples[technique].append(prompt[:60] + '...')
    
    print("Improved Categorization Results:")
    print("=" * 60)
    total = sum(technique_counts.values())
    
    for technique, count in sorted(technique_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        print(f"\n{technique}: {count} ({percentage:.1f}%)")
        for ex in examples[technique]:
            print(f"  - {ex}")