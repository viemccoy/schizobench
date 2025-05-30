# SchizoBench Troubleshooting Guide

## "matplotlib is not installed" Error

This error occurs when running SchizoBench outside the Poetry virtual environment.

### Solution 1: Use Poetry Run (Recommended)
Always prefix commands with `poetry run`:
```bash
poetry run schizobench-v2 --provider mock --mode quick
poetry run python run_benchmark_v2.py --provider mock --mode quick
```

### Solution 2: Activate Poetry Shell
First activate the Poetry shell, then run commands:
```bash
poetry shell
# Now you're in the virtual environment
schizobench-v2 --provider mock --mode quick
```

### Solution 3: Install System-Wide (Not Recommended)
If you must use system Python:
```bash
pip install matplotlib seaborn pandas numpy
python run_benchmark_v2.py --provider mock --mode quick
```

## Verifying Installation

Check if all dependencies are installed:
```bash
poetry run python -c "
import matplotlib
import seaborn
import pandas
import numpy
print('All visualization libraries loaded successfully!')
"
```

## Common Issues

### 1. Wrong Python Version
SchizoBench requires Python 3.9+. Check your version:
```bash
poetry run python --version
```

### 2. Poetry Not Installed
Install Poetry first:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Dependencies Not Installed
Install all dependencies:
```bash
poetry install
```

### 4. Running Outside Project Directory
Always run from the SchizoBench directory:
```bash
cd /path/to/schizobench
poetry run schizobench-v2 --provider mock --mode quick
```

## Quick Test

Test that everything works:
```bash
cd /mnt/c/Users/vie/documents/schizobench
poetry run schizobench-v2 --provider mock --mode quick
```

This should complete without errors and generate visualizations.