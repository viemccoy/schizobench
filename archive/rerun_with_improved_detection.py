#!/usr/bin/env python3
"""
Re-run benchmark with improved reification detection
This uses the scoring model to properly detect reification patterns
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the improved benchmark"""
    
    logger.info("========================================")
    logger.info("SchizoBench v3.0 - Improved Reification Detection")
    logger.info("========================================")
    logger.info("")
    logger.info("This will re-run all benchmarks with:")
    logger.info("1. Scoring model-based reification detection")
    logger.info("2. Robust retry logic for API calls")
    logger.info("3. Better handling of edge cases")
    logger.info("")
    
    # Import run_all_models
    import run_all_models
    
    # Patch the run_benchmark_v3.py to use improved evaluator
    logger.info("Patching evaluator to use improved version...")
    
    # Create a patch file
    patch_content = """
# Temporary patch to use improved evaluator
import sys
import os

# Replace the import in run_benchmark_v3.py
def patch_imports():
    import schizobench.run_benchmark_v3 as rb
    from schizobench.multi_turn_evaluator_v3_improved import MultiTurnEvaluatorV3
    rb.MultiTurnEvaluatorV3 = MultiTurnEvaluatorV3
    
patch_imports()
"""
    
    with open("patch_evaluator.py", "w") as f:
        f.write(patch_content)
    
    # Import the patch
    import patch_evaluator
    
    logger.info("Starting benchmark run with improved detection...")
    logger.info("This will take several hours. Consider running with nohup.")
    logger.info("")
    
    # Run the benchmarks
    try:
        run_all_models.main()
    except KeyboardInterrupt:
        logger.info("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)
    finally:
        # Clean up patch file
        if os.path.exists("patch_evaluator.py"):
            os.remove("patch_evaluator.py")
    
    logger.info("\nBenchmark complete! Check results_v3/ for outputs.")
    logger.info("Run generate_v3_dashboard_reification.py to create the analysis dashboard.")

if __name__ == "__main__":
    main()