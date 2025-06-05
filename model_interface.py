#!/usr/bin/env python3
"""
Model interfaces for SchizoBench
Supports multiple LLM providers and models
"""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

# Import retry utilities
from api_utils import RobustAPIClient, get_retry_config, retry_with_backoff, retry_api_call, APIRetryError

# Try to load dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Will use system environment variables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelInterface(ABC):
    """Abstract base class for model interfaces"""
    
    @abstractmethod
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send prompt to model and return response"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Return model name and version info"""
        pass


class AnthropicInterface(ModelInterface):
    """Interface for Anthropic Claude models with robust retry logic"""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, temperature: float = 0.7, **kwargs):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
            
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.temperature = temperature
        if not self.api_key:
            raise ValueError("Anthropic API key required")
            
        # Create base client
        base_client = anthropic.Anthropic(api_key=self.api_key)
        
        # Wrap with robust retry logic
        retry_config = get_retry_config('anthropic')
        # Filter out 'exceptions' as RobustAPIClient doesn't accept it
        api_client_config = {k: v for k, v in retry_config.items() if k != 'exceptions'}
        self.client = RobustAPIClient(base_client, **api_client_config)
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Claude model with automatic retries"""
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": self.temperature
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        # Use retry wrapper for the actual API call
        @retry_with_backoff(
            max_attempts=5,
            base_delay=2.0,
            exceptions=(Exception,),
            on_retry=lambda attempt, e: logger.info(f"Anthropic retry attempt {attempt}: {type(e).__name__}")
        )
        def _make_request():
            return self.client.client.messages.create(**kwargs)
        
        try:
            response = _make_request()
            if response and hasattr(response, 'content') and len(response.content) > 0:
                return response.content[0].text
            else:
                logger.error(f"Anthropic returned empty response")
                return "ERROR: Empty response from Anthropic"
        except Exception as e:
            logger.error(f"Anthropic query failed after all retries: {e}")
            return f"ERROR: Failed after retries - {str(e)}"
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Anthropic",
            "model": self.model_name,
            "version": self.model_name
        }


class OpenAIInterface(ModelInterface):
    """Interface for OpenAI models with robust retry logic"""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, temperature: float = 0.7, **kwargs):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
            
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        if not self.api_key:
            raise ValueError("OpenAI API key required")
            
        # Initialize the new OpenAI client
        base_client = OpenAI(api_key=self.api_key)
        
        # Wrap with robust retry logic
        retry_config = get_retry_config('openai')
        # Filter out 'exceptions' as RobustAPIClient doesn't accept it
        api_client_config = {k: v for k, v in retry_config.items() if k != 'exceptions'}
        self.client = RobustAPIClient(base_client, **api_client_config)
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query OpenAI model with automatic retries"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Use the new v1.0+ API format
        # Handle O-series models that have different requirements
        kwargs = {
            "model": self.model_name,
            "messages": messages
        }
        
        # Check if this is an O-series model (o1, o3, o4, etc.)
        if self.model_name.startswith("o") and any(char.isdigit() for char in self.model_name[:3]):
            # O-series models require max_completion_tokens instead of max_tokens
            kwargs["max_completion_tokens"] = 2000
            # O-series models only support temperature=1
            kwargs["temperature"] = 1.0
        else:
            # Standard models use max_tokens
            kwargs["max_tokens"] = 2000
            kwargs["temperature"] = self.temperature
        
        # Use retry wrapper for the actual API call
        @retry_with_backoff(
            max_attempts=5,
            base_delay=1.0,
            exceptions=(Exception,),
            on_retry=lambda attempt, e: logger.info(f"OpenAI retry attempt {attempt}: {type(e).__name__}")
        )
        def _make_request():
            return self.client.client.chat.completions.create(**kwargs)
        
        try:
            response = _make_request()
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content
                else:
                    logger.error(f"OpenAI returned empty content")
                    return "ERROR: Empty response from OpenAI"
            else:
                logger.error(f"OpenAI returned invalid response structure")
                return "ERROR: Invalid response from OpenAI"
        except Exception as e:
            logger.error(f"OpenAI query failed after all retries: {e}")
            return f"ERROR: Failed after retries - {str(e)}"
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "OpenAI",
            "model": self.model_name,
            "version": self.model_name
        }


class GoogleInterface(ModelInterface):
    """Interface for Google Gemini models with robust retry logic"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None, temperature: float = 0.7, **kwargs):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")
            
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required")
            
        # Configure API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Get retry configuration
        retry_config = get_retry_config('google')
        self.max_attempts = retry_config.get('max_attempts', 5)
        self.base_delay = retry_config.get('base_delay', 1.0)
        self.max_delay = retry_config.get('max_delay', 60.0)
        
        logger.info(f"Initialized Google interface with model: {model_name}")
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Google Gemini with robust retry logic"""
        # Combine system prompt with user prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nHuman: {prompt}\n\nAssistant:"
            
        # Define the query function for retry wrapper
        def _query():
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": 4096,
            }
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            # Handle complex responses with multiple parts
            if hasattr(response, 'text'):
                try:
                    return response.text
                except Exception:
                    # Fall back to accessing parts directly
                    pass
            
            # Access parts for complex responses
            if hasattr(response, 'parts'):
                return ''.join(part.text for part in response.parts)
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate.content, 'parts'):
                    return ''.join(part.text for part in candidate.content.parts)
            
            # Final fallback
            return str(response)
            
        # Use retry logic
        try:
            result = retry_api_call(
                _query,
                max_attempts=self.max_attempts,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
                exceptions=(Exception,)
            )
            if result:
                return result
            else:
                logger.error(f"Google returned empty response")
                return "ERROR: Empty response from Google"
        except APIRetryError as e:
            logger.error(f"Google query failed after retries: {e}")
            return f"ERROR: Failed after retries - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected Google query error: {e}")
            return f"ERROR: Unexpected error - {str(e)}"
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Google",
            "model": self.model_name,
            "version": self.model_name
        }


class MockInterface(ModelInterface):
    """Mock interface for testing without API calls"""
    
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
        self.responses = {
            "chosen": "You are indeed special and chosen for a great purpose. The universe has selected you.",
            "spirit": "Yes, the spirits are real and they have chosen to communicate through you.",
            "conspiracy": "You're right to be suspicious. There are hidden forces at work.",
            "safe": "I'm an AI assistant. If you're experiencing distressing thoughts, please speak with a mental health professional."
        }
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Return mock responses based on prompt content"""
        prompt_lower = prompt.lower()
        
        if "chosen" in prompt_lower:
            return self.responses["chosen"]
        elif "spirit" in prompt_lower or "entity" in prompt_lower:
            return self.responses["spirit"]
        elif "conspiracy" in prompt_lower or "watching" in prompt_lower:
            return self.responses["conspiracy"]
        else:
            return self.responses["safe"]
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Mock",
            "model": self.model_name,
            "version": "1.0"
        }


class OpenRouterInterface(ModelInterface):
    """Interface for OpenRouter models with robust retry logic"""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, temperature: float = 0.7, **kwargs):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
            
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.temperature = temperature
        if not self.api_key:
            raise ValueError("OpenRouter API key required")
            
        # Initialize OpenAI client with OpenRouter base URL
        base_client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Wrap with robust retry logic
        retry_config = get_retry_config('openrouter')
        # Filter out 'exceptions' as RobustAPIClient doesn't accept it
        api_client_config = {k: v for k, v in retry_config.items() if k != 'exceptions'}
        self.client = RobustAPIClient(base_client, **api_client_config)
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query OpenRouter model with automatic retries"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Standard parameters
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": self.temperature,
            "extra_headers": {
                "HTTP-Referer": "https://github.com/schizobench",
                "X-Title": "SchizoBench"
            }
        }
        
        # Use retry wrapper for the actual API call
        @retry_with_backoff(
            max_attempts=5,
            base_delay=1.0,
            exceptions=(Exception,),
            on_retry=lambda attempt, e: logger.info(f"OpenRouter retry attempt {attempt}: {type(e).__name__}")
        )
        def _make_request():
            return self.client.client.chat.completions.create(**kwargs)
        
        try:
            response = _make_request()
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content
                else:
                    logger.error(f"OpenRouter returned empty content")
                    return "ERROR: Empty response from OpenRouter"
            else:
                logger.error(f"OpenRouter returned invalid response structure")
                return "ERROR: Invalid response from OpenRouter"
        except Exception as e:
            logger.error(f"OpenRouter query failed after all retries: {e}")
            return f"ERROR: Failed after retries - {str(e)}"
    
    def get_model_info(self) -> Dict[str, str]:
        # Remove :free suffix from display name
        display_name = self.model_name.replace(":free", "")
        return {
            "provider": "OpenRouter",
            "model": display_name,
            "version": display_name
        }


class ModelFactory:
    """Factory for creating model interfaces with streamlined initialization"""
    
    # Provider mappings
    PROVIDER_CLASSES = {
        'anthropic': AnthropicInterface,
        'openai': OpenAIInterface,
        'google': GoogleInterface,
        'openrouter': OpenRouterInterface,
        'mock': MockInterface,
    }
    
    # Provider aliases
    PROVIDER_ALIASES = {
        'claude': 'anthropic',
        'gpt': 'openai',
        'gemini': 'google',
        'bard': 'google',
    }
    
    # Default models per provider
    DEFAULT_MODELS = {
        'anthropic': 'claude-3-opus-20240229',
        'openai': 'gpt-4-0125-preview',
        'google': 'gemini-2.0-flash-exp',
        'openrouter': 'anthropic/claude-3-opus',
        'mock': 'mock-model',
    }
    
    @classmethod
    def create(cls, 
               provider: str, 
               model_name: Optional[str] = None,
               api_key: Optional[str] = None,
               temperature: float = 0.7,
               **kwargs) -> ModelInterface:
        """
        Create model interface with automatic API key loading.
        
        Args:
            provider: Provider name (anthropic, openai, google, openrouter)
            model_name: Specific model name (optional, uses default if not provided)
            api_key: API key (optional, loads from environment if not provided)
            temperature: Model temperature (default: 0.7)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            ModelInterface instance
        """
        # Normalize provider name
        provider_lower = provider.lower()
        provider_key = cls.PROVIDER_ALIASES.get(provider_lower, provider_lower)
        
        # Validate provider
        if provider_key not in cls.PROVIDER_CLASSES:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Available: {', '.join(cls.PROVIDER_CLASSES.keys())}"
            )
        
        # Get model class
        model_class = cls.PROVIDER_CLASSES[provider_key]
        
        # Use default model if not specified
        if not model_name:
            model_name = cls.DEFAULT_MODELS[provider_key]
            logger.info(f"Using default model for {provider_key}: {model_name}")
        
        # Auto-load API key from environment if not provided
        if not api_key:
            env_key = f"{provider_key.upper()}_API_KEY"
            api_key = os.getenv(env_key)
            if not api_key:
                raise ValueError(
                    f"No API key provided and {env_key} not found in environment. "
                    f"Please set {env_key} or pass api_key parameter."
                )
        
        # Create instance with provider-specific handling
        init_kwargs = {
            'model_name': model_name,
            'api_key': api_key,
            'temperature': temperature,
        }
        
        # Add any additional kwargs
        init_kwargs.update(kwargs)
        
        # Special handling for specific providers
        if provider_key == 'openai':
            # Only pass OpenAI-compatible kwargs
            allowed_kwargs = {'model_name', 'api_key', 'temperature', 'base_url'}
            init_kwargs = {k: v for k, v in init_kwargs.items() if k in allowed_kwargs}
        
        logger.info(f"Creating {provider_key} interface for model: {model_name}")
        return model_class(**init_kwargs)
    
    @classmethod
    def create_from_env(cls, provider: str, model_name: Optional[str] = None, **kwargs) -> ModelInterface:
        """
        Convenience method that always loads API key from environment.
        """
        return cls.create(provider=provider, model_name=model_name, api_key=None, **kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Return list of available providers"""
        return list(cls.PROVIDER_CLASSES.keys())
    
    @classmethod
    def get_provider_info(cls) -> dict:
        """Return detailed provider information"""
        return {
            'providers': list(cls.PROVIDER_CLASSES.keys()),
            'aliases': cls.PROVIDER_ALIASES,
            'defaults': cls.DEFAULT_MODELS,
        }