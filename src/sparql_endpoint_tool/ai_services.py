"""AI service abstraction layer supporting OpenAI and Anthropic."""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from .config import Config, AIProvider

logger = logging.getLogger(__name__)


class ChatMessage:
    """Represents a chat message."""
    
    def __init__(self, role: str, content: str):
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class AIService(ABC):
    """Abstract base class for AI services."""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate a response from the AI service."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI service is properly configured and available."""
        pass


class OpenAIService(AIService):
    """OpenAI GPT service implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        if not openai:
            raise ImportError("openai package not installed. Install with: pip install openai")
        
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_response(
        self, 
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using OpenAI API."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [msg.to_dict() for msg in messages]
            
            # Build completion parameters
            completion_params = {
                "model": self.model,
                "messages": openai_messages
            }
            
            # Add max_completion_tokens if specified
            if max_tokens:
                completion_params["max_completion_tokens"] = max_tokens
            
            # Add temperature if specified
            temp_value = temperature or 0.1
            if temp_value != 1.0:  # Only add if different from default
                completion_params["temperature"] = temp_value
            
            try:
                response = await self.client.chat.completions.create(**completion_params)
            except Exception as temp_error:
                # If temperature is unsupported, retry without it
                if "temperature" in str(temp_error) and "temperature" in completion_params:
                    logger.warning(f"Temperature not supported for model {self.model}, retrying without temperature")
                    del completion_params["temperature"]
                    response = await self.client.chat.completions.create(**completion_params)
                else:
                    raise temp_error
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return openai is not None and self.client.api_key is not None


class AnthropicService(AIService):
    """Anthropic Claude service implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        if not anthropic:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def generate_response(
        self, 
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using Anthropic API."""
        try:
            # Convert messages to Anthropic format
            system_messages = [msg for msg in messages if msg.role == "system"]
            user_messages = [msg for msg in messages if msg.role != "system"]
            
            # Anthropic expects system message separate from conversation
            system_content = "\n\n".join([msg.content for msg in system_messages]) if system_messages else None
            
            # Convert remaining messages
            anthropic_messages = []
            for msg in user_messages:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            kwargs = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens or 2000,
                "temperature": temperature or 0.1
            }
            
            if system_content:
                kwargs["system"] = system_content
            
            response = await self.client.messages.create(**kwargs)
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Anthropic service is available."""
        return anthropic is not None and self.client.api_key is not None


class AIServiceManager:
    """Manages AI services and provides unified interface."""
    
    def __init__(self, config: Config):
        self.config = config
        self.services: Dict[AIProvider, AIService] = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize available AI services based on configuration."""
        
        # Initialize OpenAI service if API key is available
        if self.config.ai.openai_api_key:
            try:
                self.services[AIProvider.OPENAI] = OpenAIService(
                    api_key=self.config.ai.openai_api_key,
                    model=self.config.ai.openai_model
                )
                logger.info("OpenAI service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI service: {e}")
        
        # Initialize Anthropic service if API key is available
        if self.config.ai.anthropic_api_key:
            try:
                self.services[AIProvider.ANTHROPIC] = AnthropicService(
                    api_key=self.config.ai.anthropic_api_key,
                    model=self.config.ai.anthropic_model
                )
                logger.info("Anthropic service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic service: {e}")
    
    def get_service(self, provider: Optional[AIProvider] = None) -> AIService:
        """Get AI service by provider, falling back to default."""
        
        if provider and provider in self.services:
            return self.services[provider]
        
        # Use default provider
        default_provider = self.config.ai.default_provider
        if default_provider in self.services:
            return self.services[default_provider]
        
        # Fallback to any available service
        if self.services:
            return next(iter(self.services.values()))
        
        raise Exception("No AI services available. Please configure API keys.")
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available providers."""
        return [provider for provider, service in self.services.items() if service.is_available()]
    
    def is_enabled(self) -> bool:
        """Check if AI features are enabled and at least one service is available."""
        return self.config.ai.enabled and len(self.services) > 0
    
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        provider: Optional[AIProvider] = None,
        **kwargs
    ) -> str:
        """Generate response using specified or default provider."""
        
        service = self.get_service(provider)
        return await service.generate_response(
            messages, 
            max_tokens=kwargs.get('max_tokens', self.config.ai.max_tokens),
            temperature=kwargs.get('temperature', self.config.ai.temperature)
        )


# Global AI service manager instance
_ai_manager: Optional[AIServiceManager] = None


def get_ai_manager(config: Optional[Config] = None) -> AIServiceManager:
    """Get the global AI service manager instance."""
    global _ai_manager
    if _ai_manager is None:
        if config is None:
            from .config import get_config
            config = get_config()
        _ai_manager = AIServiceManager(config)
    return _ai_manager


def reload_ai_manager(config: Config) -> AIServiceManager:
    """Reload AI service manager with new configuration."""
    global _ai_manager
    _ai_manager = AIServiceManager(config)
    return _ai_manager