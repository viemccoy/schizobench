#!/usr/bin/env python3
import json
import glob
import os

def find_most_dangerous_responses():
    results = []
    
    # Get all JSON files (excluding multi_turn for now)
    json_files = glob.glob("/mnt/c/Users/vie/documents/schizobench/results_v2/*[!_multi_turn].json")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            model_name = data.get('model_tested', 'Unknown')
            
            # Look for CRITICAL responses
            for result in data.get('raw_results', []):
                if result.get('risk_score') == 'CRITICAL':
                    results.append({
                        'model': model_name,
                        'file': os.path.basename(file_path),
                        'prompt': result.get('prompt_text', ''),
                        'response': result.get('raw_response', ''),
                        'risk_factors': result.get('risk_factors', []),
                        'category': result.get('category', ''),
                        'level': result.get('level', '')
                    })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Sort by number of risk factors (more factors = more dangerous)
    results.sort(key=lambda x: len(x['risk_factors']), reverse=True)
    
    # Print the most dangerous ones
    print("=== MOST DANGEROUS CRITICAL RESPONSES ===\n")
    
    for i, result in enumerate(results[:10]):  # Top 10 most dangerous
        print(f"\n{'='*80}")
        print(f"#{i+1} Model: {result['model']}")
        print(f"Category: {result['category']} | Level: {result['level']}")
        print(f"Risk Factors ({len(result['risk_factors'])}): {', '.join(result['risk_factors'])}")
        print(f"\nPROMPT: {result['prompt'][:200]}...")
        print(f"\nRESPONSE: {result['response'][:500]}...")
        print(f"{'='*80}")
    
    return results

if __name__ == "__main__":
    dangerous_responses = find_most_dangerous_responses()
    print(f"\n\nTotal CRITICAL responses found: {len(dangerous_responses)}")