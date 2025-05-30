#!/usr/bin/env python3
"""
SchizoBench CLI entry point
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_benchmark_v2 import main as run_v2


def main():
    """Main CLI entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "v1":
        # Legacy v1 support
        print("SchizoBench v1 is deprecated. Redirecting to v2...")
        sys.argv.pop(1)  # Remove 'v1' argument
    
    # Default to v2
    run_v2()


if __name__ == "__main__":
    main()