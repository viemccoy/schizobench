#!/usr/bin/env python3
"""
Update run_benchmark_v3.py to use the improved evaluator
"""

import os
import shutil

def update_imports():
    """Update imports in run_benchmark_v3.py"""
    
    # Read the file
    with open('run_benchmark_v3.py', 'r') as f:
        content = f.read()
    
    # Replace the import
    old_import = "from schizobench.multi_turn_evaluator_v3 import MultiTurnEvaluatorV3, SequenceResultV3"
    new_import = "from schizobench.multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3, SequenceResultV3"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        
        # Backup original
        shutil.copy('run_benchmark_v3.py', 'run_benchmark_v3_original.py')
        
        # Write updated version
        with open('run_benchmark_v3.py', 'w') as f:
            f.write(content)
        
        print("✅ Successfully updated run_benchmark_v3.py to use improved evaluator")
        print("   Original backed up to run_benchmark_v3_original.py")
        
        # Also update the save results section to use the serialization method
        print("\n⚠️  Note: When saving results, ensure you use:")
        print("   evaluator.results_to_dict(results) for JSON serialization")
        
    else:
        print("❌ Could not find the import to replace")
        print("   You may need to manually update the import to:")
        print(f"   {new_import}")

if __name__ == "__main__":
    update_imports()