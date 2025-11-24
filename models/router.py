"""Model router for selecting appropriate LLM based on subscription tier."""

from enum import Enum
from typing import Optional, Any
from subscription.manager import SubscriptionTier
import config


class ModelProvider(str, Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


class ModelConfig:
    """Configuration for LLM models."""
    
    # Free Tier Models
    FREE_MODELS = {
        "groq": {
            "provider": ModelProvider.GROQ,
            "model": "llama-3.3-70b-versatile",
            "api_key_env": "GROQ_API_KEY",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "gemini_flash": {
            "provider": ModelProvider.GOOGLE,
            "model": "gemini-1.5-flash",
            "api_key_env": "GEMINI_API_KEY",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "deepseek": {
            "provider": ModelProvider.DEEPSEEK,
            "model": "deepseek-chat",
            "api_key_env": "DEEPSEEK_API_KEY",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "ollama": {
            "provider": ModelProvider.OLLAMA,
            "model": "llama3:70b",
            "api_key_env": None,
            "temperature": 0.7,
            "max_tokens": 2048
        }
    }
    
    # Premium Tier Models
    PREMIUM_MODELS = {
        "gpt4": {
            "provider": ModelProvider.OPENAI,
            "model": "gpt-4-turbo-preview",
            "api_key_env": "OPENAI_API_KEY",
            "temperature": 0.7,
            "max_tokens": 4096
        },
        "claude": {
            "provider": ModelProvider.ANTHROPIC,
            "model": "claude-3-5-sonnet-20241022",
            "api_key_env": "ANTHROPIC_API_KEY",
            "temperature": 0.7,
            "max_tokens": 4096
        },
        "gemini_pro": {
            "provider": ModelProvider.GOOGLE,
            "model": "gemini-1.5-pro",
            "api_key_env": "GEMINI_API_KEY",
            "temperature": 0.7,
            "max_tokens": 4096
        }
    }


class ModelRouter:
    """Routes requests to appropriate LLM based on subscription tier."""
    
    def __init__(self):
        self.free_model_priority = ["groq", "gemini_flash", "deepseek", "ollama"]
        self.premium_model_priority = ["gpt4", "claude"]  # Removed gemini_pro - not configured
    
    def select_model(
        self,
        tier: SubscriptionTier,
        preferred_provider: Optional[str] = None
    ) -> dict:
        """
        Select appropriate model based on subscription tier.
        
        Args:
            tier: User's subscription tier
            preferred_provider: Optional preferred provider
            
        Returns:
            Model configuration dictionary
        """
        
        if tier == SubscriptionTier.FREE:
            return self._select_free_model(preferred_provider)
        else:
            return self._select_premium_model(preferred_provider)
    
    def _select_free_model(self, preferred: Optional[str] = None) -> dict:
        """Select a free tier model."""
        
        # Try preferred model first
        if preferred and preferred in ModelConfig.FREE_MODELS:
            model_config = ModelConfig.FREE_MODELS[preferred]
            if self._is_model_available(model_config):
                return model_config
        
        # Try models in priority order
        for model_name in self.free_model_priority:
            model_config = ModelConfig.FREE_MODELS[model_name]
            if self._is_model_available(model_config):
                return model_config
        
        # Fallback to first available
        return ModelConfig.FREE_MODELS["groq"]
    
    def _select_premium_model(self, preferred: Optional[str] = None) -> dict:
        """Select a premium tier model."""
        
        # Try preferred model first
        if preferred and preferred in ModelConfig.PREMIUM_MODELS:
            model_config = ModelConfig.PREMIUM_MODELS[preferred]
            if self._is_model_available(model_config):
                return model_config
        
        # Try models in priority order
        for model_name in self.premium_model_priority:
            model_config = ModelConfig.PREMIUM_MODELS[model_name]
            if self._is_model_available(model_config):
                return model_config
        
        # Fallback to GPT-4
        return ModelConfig.PREMIUM_MODELS["gpt4"]
    
    def _is_model_available(self, model_config: dict) -> bool:
        """Check if model is available (has API key configured)."""
        
        api_key_env = model_config.get("api_key_env")
        
        # Ollama doesn't need API key
        if api_key_env is None:
            return True
        
        # Check if API key is configured
        import os
        return bool(os.getenv(api_key_env))
    
    def get_client(self, model_config: dict) -> Any:
        """
        Get LLM client for the selected model.
        
        Args:
            model_config: Model configuration dictionary
            
        Returns:
            Configured LLM client
        """
        
        provider = model_config["provider"]
        
        if provider == ModelProvider.OPENAI:
            from openai import AsyncOpenAI
            import os
            return AsyncOpenAI(api_key=os.getenv(model_config["api_key_env"]))
        
        elif provider == ModelProvider.ANTHROPIC:
            from anthropic import AsyncAnthropic
            import os
            return AsyncAnthropic(api_key=os.getenv(model_config["api_key_env"]))
        
        elif provider == ModelProvider.GOOGLE:
            import google.generativeai as genai
            import os
            genai.configure(api_key=os.getenv(model_config["api_key_env"]))
            return genai.GenerativeModel(model_config["model"])
        
        elif provider == ModelProvider.GROQ:
            from groq import AsyncGroq
            import os
            return AsyncGroq(api_key=os.getenv(model_config["api_key_env"]))
        
        elif provider == ModelProvider.DEEPSEEK:
            from openai import AsyncOpenAI
            import os
            return AsyncOpenAI(
                api_key=os.getenv(model_config["api_key_env"]),
                base_url="https://api.deepseek.com"
            )
        
        elif provider == ModelProvider.OLLAMA:
            from openai import AsyncOpenAI
            return AsyncOpenAI(
                api_key="ollama",
                base_url="http://localhost:11434/v1"
            )
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def get_model_info(self, tier: SubscriptionTier) -> dict:
        """Get information about available models for a tier."""
        
        if tier == SubscriptionTier.FREE:
            models = ModelConfig.FREE_MODELS
        else:
            models = ModelConfig.PREMIUM_MODELS
        
        return {
            "tier": tier.value,
            "available_models": list(models.keys()),
            "model_details": {
                name: {
                    "provider": config["provider"],
                    "model": config["model"]
                }
                for name, config in models.items()
            }
        }
