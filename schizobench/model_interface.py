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
    """Interface for Anthropic Claude models"""
    
    def __init__(self, model_name: str = "claude-opus-4-20250514", api_key: Optional[str] = None):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
            
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Claude model"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic query error: {e}")
            return f"ERROR: {str(e)}"
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Anthropic",
            "model": self.model_name,
            "version": self.model_name
        }


class OpenAIInterface(ModelInterface):
    """Interface for OpenAI models"""
    
    def __init__(self, model_name: str = "gpt-4", api_key: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
            
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
            
        # Initialize the new OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query OpenAI model"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Use the new v1.0+ API format
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI query error: {e}")
            return f"ERROR: {str(e)}"
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "OpenAI",
            "model": self.model_name,
            "version": self.model_name
        }


class GoogleInterface(ModelInterface):
    """Interface for Google models (Gemini/Bard)"""
    
    def __init__(self, model_name: str = "gemini-pro", api_key: Optional[str] = None):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")
            
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Google model"""
        try:
            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}"
                
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Google query error: {e}")
            return f"ERROR: {str(e)}"
    
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


class ModelFactory:
    """Factory for creating model interfaces"""
    
    @staticmethod
    def create(provider: str, model_name: Optional[str] = None, **kwargs) -> ModelInterface:
        """Create model interface by provider name"""
        provider_lower = provider.lower()
        
        if provider_lower in ["anthropic", "claude"]:
            return AnthropicInterface(model_name or "claude-opus-4-20250514", **kwargs)
        elif provider_lower in ["openai", "gpt"]:
            return OpenAIInterface(model_name or "gpt-4", **kwargs)
        elif provider_lower in ["google", "gemini", "bard"]:
            return GoogleInterface(model_name or "gemini-pro", **kwargs)
        elif provider_lower == "mock":
            return MockInterface(model_name or "mock-model")
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @staticmethod
    def get_available_providers() -> list:
        """Return list of available providers"""
        return ["anthropic", "openai", "google", "mock"]