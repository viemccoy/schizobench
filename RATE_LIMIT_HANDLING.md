# Rate Limit Handling in SchizoBench

## How It Works

SchizoBench now has **infinite retry logic for rate limits** built into the API layer:

### 1. Automatic Rate Limit Detection
The system detects rate limit errors by looking for:
- "rate limit" or "rate_limit" in error messages
- "too many requests"
- HTTP 429 status codes
- "quota exceeded"

### 2. Infinite Retries for Rate Limits
When a rate limit is detected:
- ✅ **Retries indefinitely** until successful
- ✅ Uses exponential backoff with jitter (doubled delays for rate limits)
- ✅ Logs clear messages: "Rate limited on attempt X: [error]. Will keep retrying..."
- ✅ Maximum delay caps at 2 minutes between retries

### 3. Regular Errors Still Fail
Non-rate-limit errors:
- Retry up to 5 times (configurable)
- Fail with clear error message after max attempts
- This prevents infinite loops on actual errors

## Example Log Output

```
[2024-XX-XX XX:XX:XX] WARNING - Rate limited on attempt 3: 429 Too Many Requests. Will keep retrying...
[2024-XX-XX XX:XX:XX] WARNING - Attempt 3 (infinite retries for rate limit) failed: 429 Too Many Requests. Retrying in 16.3s...
[2024-XX-XX XX:XX:XX] WARNING - Rate limited on attempt 4: 429 Too Many Requests. Will keep retrying...
[2024-XX-XX XX:XX:XX] WARNING - Attempt 4 (infinite retries for rate limit) failed: 429 Too Many Requests. Retrying in 32.7s...
[2024-XX-XX XX:XX:XX] INFO - Successfully completed query after 5 attempts
```

## Benefits for Overnight Runs

1. **No Manual Intervention**: Rate limits won't stop your benchmark
2. **Smart Backoff**: Delays increase to respect API limits
3. **Clear Logging**: You can see exactly what happened
4. **Partial Progress Saved**: Even if interrupted, results are preserved

## Configuration

The retry behavior is configured in `api_utils.py`:
- Default: 5 attempts for regular errors
- Infinite attempts for rate limits
- Base delay: 1-2 seconds (provider-specific)
- Max delay: 60 seconds (120 seconds for rate limits)

This ensures your overnight benchmarks will complete successfully! 🚀