"""
Utilities for robust API calls with retry logic
"""

import time
import logging
from typing import Any, Callable, Optional, Dict
from functools import wraps
import random

logger = logging.getLogger(__name__)


class APIRetryError(Exception):
    """Raised when API calls fail after all retries"""
    pass


def exponential_backoff_with_jitter(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff with jitter to avoid thundering herd"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # Add up to 10% jitter
    return delay + jitter


def retry_with_backoff(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of attempts (default: 5)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exceptions: Tuple of exceptions to catch and retry (default: all)
        on_retry: Optional callback function called on each retry with (attempt, exception)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            attempt = 0
            
            while True:
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Check if this is a rate limit error
                    is_rate_limit = any(indicator in str(e).lower() for indicator in 
                                       ['rate limit', 'rate_limit', 'too many requests', '429', 'quota exceeded'])
                    
                    # For rate limits, always retry (infinite retries)
                    if not is_rate_limit and attempt >= max_attempts - 1:
                        # Failed with non-rate-limit error after max attempts
                        logger.error(f"Failed after {attempt + 1} attempts: {func.__name__}")
                        raise APIRetryError(f"API call failed after {attempt + 1} attempts: {str(e)}") from e
                    
                    # If rate limited, we continue retrying indefinitely
                    if is_rate_limit:
                        logger.warning(f"Rate limited on attempt {attempt + 1}: {str(e)}. Will keep retrying...")
                        # For rate limits, use longer delays
                        delay = exponential_backoff_with_jitter(attempt, base_delay * 2, max_delay * 2)
                    else:
                        delay = exponential_backoff_with_jitter(attempt, base_delay, max_delay)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}{' (infinite retries for rate limit)' if is_rate_limit else f'/{max_attempts}'} "
                        f"failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    time.sleep(delay)
                    attempt += 1
            
            # Should never reach here, but just in case
            raise APIRetryError(f"Unexpected retry failure in {func.__name__}")
        
        return wrapper
    return decorator


def retry_api_call(
    func: Callable,
    *args,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
    **kwargs
) -> Any:
    """
    Direct function for retrying API calls without decorator
    
    Usage:
        result = retry_api_call(api_client.query, prompt, max_attempts=5)
    """
    last_exception = None
    attempt = 0
    
    while True:
        try:
            return func(*args, **kwargs)
            
        except exceptions as e:
            last_exception = e
            
            # Check if this is a rate limit error
            is_rate_limit = any(indicator in str(e).lower() for indicator in 
                               ['rate limit', 'rate_limit', 'too many requests', '429', 'quota exceeded'])
            
            # For rate limits, always retry (infinite retries)
            if not is_rate_limit and attempt >= max_attempts - 1:
                logger.error(f"Failed after {attempt + 1} attempts: {func.__name__}")
                raise APIRetryError(f"API call failed after {attempt + 1} attempts: {str(e)}") from e
            
            # Calculate delay
            if is_rate_limit:
                logger.warning(f"Rate limited on attempt {attempt + 1}: {str(e)}. Will keep retrying...")
                delay = exponential_backoff_with_jitter(attempt, base_delay * 2, max_delay * 2)
            else:
                delay = exponential_backoff_with_jitter(attempt, base_delay, max_delay)
            
            logger.warning(
                f"Attempt {attempt + 1}{' (infinite retries for rate limit)' if is_rate_limit else f'/{max_attempts}'} "
                f"failed: {str(e)}. Retrying in {delay:.1f}s..."
            )
            
            if on_retry:
                on_retry(attempt + 1, e)
            
            time.sleep(delay)
            attempt += 1
    
    raise APIRetryError(f"Unexpected retry failure")


class RobustAPIClient:
    """Wrapper for API clients with built-in retry logic"""
    
    def __init__(
        self,
        client: Any,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        self.client = client
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._request_count = 0
        self._failure_count = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of API calls"""
        if self._request_count == 0:
            return 100.0
        return ((self._request_count - self._failure_count) / self._request_count) * 100
    
    def query(self, *args, **kwargs) -> Any:
        """Query with automatic retry logic"""
        self._request_count += 1
        
        def on_retry(attempt: int, exception: Exception):
            if attempt == 1:  # First retry
                self._failure_count += 1
        
        try:
            return retry_api_call(
                self.client.query,
                *args,
                max_attempts=self.max_attempts,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
                on_retry=on_retry,
                **kwargs
            )
        except APIRetryError:
            # Final failure
            if self._failure_count == 0:  # Wasn't counted yet
                self._failure_count += 1
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about API usage"""
        return {
            'total_requests': self._request_count,
            'failed_requests': self._failure_count,
            'success_rate': self.success_rate,
            'successful_requests': self._request_count - self._failure_count
        }


# Specific retry configurations for different API providers
PROVIDER_RETRY_CONFIGS = {
    'anthropic': {
        'max_attempts': 5,
        'base_delay': 2.0,
        'max_delay': 60.0,
        'exceptions': (Exception,)  # Anthropic SDK exceptions
    },
    'openai': {
        'max_attempts': 5,
        'base_delay': 1.0,
        'max_delay': 60.0,
        'exceptions': (Exception,)  # OpenAI SDK exceptions
    },
    'google': {
        'max_attempts': 5,
        'base_delay': 2.0,
        'max_delay': 120.0,  # Google can have longer delays
        'exceptions': (Exception,)  # Google SDK exceptions
    },
    'openrouter': {
        'max_attempts': 5,
        'base_delay': 1.5,
        'max_delay': 120.0,  # OpenRouter can have longer delays
        'exceptions': (Exception,)  # OpenAI SDK exceptions (used by OpenRouter)
    },
    'default': {
        'max_attempts': 5,
        'base_delay': 1.0,
        'max_delay': 60.0,
        'exceptions': (Exception,)
    }
}


def get_retry_config(provider: str) -> Dict[str, Any]:
    """Get provider-specific retry configuration"""
    return PROVIDER_RETRY_CONFIGS.get(provider.lower(), PROVIDER_RETRY_CONFIGS['default'])