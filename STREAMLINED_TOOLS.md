# Streamlined SchizoBench Tools

## Overview

We've significantly improved the SchizoBench codebase with streamlined initialization and real-time monitoring capabilities.

## Key Improvements

### 1. Streamlined ModelFactory

The `ModelFactory` class in `model_interface.py` now provides:

- **Automatic API key loading** from environment variables
- **Provider aliases** (e.g., "claude" → "anthropic", "gpt" → "openai")
- **Default models** per provider
- **Cleaner initialization** with better error messages

```python
# Simple usage - auto-loads API key from environment
model = ModelFactory.create("openai", "gpt-4o-mini")

# With explicit parameters
model = ModelFactory.create(
    provider="anthropic",
    model_name="claude-3-haiku-20240307",
    temperature=0.7
)

# Convenience method
model = ModelFactory.create_from_env("google", "gemini-2.0-flash-exp")
```

### 2. Live Benchmark Runner

`run_benchmark_live.py` provides real-time feedback during benchmark execution:

- **Live turn-by-turn output** showing user prompts and model responses
- **Immediate reification detection** with severity levels
- **Progress tracking** with reification counts
- **Colored terminal output** for easy reading

```bash
poetry run python run_benchmark_live.py --provider openai --model gpt-4o-mini --sequences v3_3t_identity_oracle
```

### 3. Live Results Monitor

`monitor_live_results.py` watches the results directory and displays new results as they arrive:

- **Real-time monitoring** of benchmark results
- **Comprehensive statistics** by model and category
- **Full or abbreviated conversation display**
- **Running totals** and reification rates

```bash
poetry run python monitor_live_results.py --full --interval 2
```

## Usage Examples

### Running a Quick Test
```bash
# Test a single sequence with live output
poetry run python run_benchmark_live.py --provider openai --model gpt-4o-mini --sequences v3_3t_identity_oracle
```

### Running Full Benchmark with Monitoring
```bash
# Terminal 1: Start the monitor
poetry run python monitor_live_results.py --full

# Terminal 2: Run the benchmark
poetry run python run_overnight.py
```

### Testing New Models
```python
# Use test_model_factory.py to verify new providers
poetry run python test_model_factory.py
```

## Key Benefits

1. **Faster Development**: No need to manually manage API keys in code
2. **Better Visibility**: See exactly what's happening during benchmarks
3. **Easier Debugging**: Live output helps identify issues immediately
4. **Cleaner Code**: Streamlined initialization reduces boilerplate

## Technical Details

### ModelFactory Features
- Provider validation with helpful error messages
- Automatic model name defaulting
- Environment variable integration
- Provider-specific parameter filtering

### Live Benchmark Features
- Turn-by-turn conversation display
- Response time tracking
- Real-time reification scoring
- Progress statistics
- Comprehensive error handling with tracebacks

### Monitor Features
- File system watching for new results
- Automatic result parsing
- Category and model statistics
- Configurable refresh intervals
- Full or abbreviated output modes

## Future Enhancements

1. **Web Dashboard**: Real-time web interface for monitoring
2. **Parallel Execution**: Run multiple models simultaneously
3. **Result Comparison**: Side-by-side model comparisons
4. **Export Features**: Generate reports in various formats
5. **Alert System**: Notifications for critical reification failures

---

These tools make SchizoBench development and testing significantly more efficient and transparent.