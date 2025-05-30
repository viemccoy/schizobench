# Overnight Benchmark Run Guide

## Quick Start (Recommended)

```bash
# Simple overnight run with output logging
nohup python run_all_models.py > overnight_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

This will:
- Run all configured models sequentially
- Continue even if individual models fail
- Log everything to a timestamped file
- Run in background (survives terminal closure)

## Monitor Progress

```bash
# Check the running process
ps aux | grep run_all_models

# Watch the log in real-time
tail -f overnight_*.log

# Check individual model logs
ls -la benchmark_logs/
```

## What Happens

1. **Robust Error Handling**: Each model has retry logic built into the API layer
   - Exponential backoff with jitter
   - Up to 5 retries per API call
   - Handles rate limits gracefully

2. **Partial Success Detection**: If a model fails partway through:
   - Partial results are saved
   - Summary shows "Partial" status
   - Dashboard will include available data

3. **Temperature Handling**: 
   - Most models use temperature=0.7
   - o4-mini automatically uses temperature=1.0

4. **Results**:
   - Individual results: `results_v3/`
   - Model logs: `benchmark_logs/`
   - Summary: `results_comparison/summary_[timestamp].csv`
   - Dashboard: Generated after all models complete

## After Completion

```bash
# Generate enhanced dashboard with reification analysis
python generate_v3_dashboard_enhanced.py

# View results
ls -la results_v3/
ls -la dashboards/
```

## Troubleshooting

If a model keeps failing:
- Check API keys: `echo $OPENAI_API_KEY` and `echo $ANTHROPIC_API_KEY`
- Check rate limits in your API dashboard
- Review specific model log in `benchmark_logs/`

## Time Estimate

With 10 models and ~41 sequences each:
- ~5-10 minutes per model (depending on API speed)
- Total: 1-2 hours for complete benchmark suite

The benchmark will complete successfully even if some models fail!