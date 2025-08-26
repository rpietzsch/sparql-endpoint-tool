"""Configuration management for SPARQL Endpoint Tool."""

import os
import toml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from enum import Enum


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIProviderConfig(BaseSettings):
    """Configuration for AI providers."""
    api_key: Optional[str] = None
    model: Optional[str] = None
    
    class Config:
        env_prefix = ""


class AIConfig(BaseSettings):
    """AI configuration settings."""
    enabled: bool = Field(default=True, description="Enable AI chat features")
    default_provider: AIProvider = Field(default=AIProvider.ANTHROPIC, description="Default AI provider")
    
    # Provider configs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", description="Anthropic model to use")
    
    max_tokens: int = Field(default=2000, description="Maximum tokens per response")
    temperature: float = Field(default=0.1, description="AI temperature setting")

    class Config:
        env_prefix = ""


class Config(BaseSettings):
    """Main configuration for SPARQL Endpoint Tool."""
    
    # Server settings
    host: str = Field(default="127.0.0.1", env="SPARQL_HOST")
    port: int = Field(default=8000, env="SPARQL_PORT")
    
    # AI settings
    ai: AIConfig = Field(default_factory=AIConfig)
    
    class Config:
        env_prefix = "SPARQL_"


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file and environment variables."""
    
    config_data = {}
    
    # Try to load from config file
    if config_path and config_path.exists():
        config_data = toml.load(config_path)
    else:
        # Look for default config files
        possible_configs = [
            Path.cwd() / "sparql-config.toml",
            Path.home() / ".config" / "sparql-endpoint-tool" / "config.toml",
            Path.home() / ".sparql-endpoint-tool.toml"
        ]
        
        for config_file in possible_configs:
            if config_file.exists():
                config_data = toml.load(config_file)
                break
    
    # Create config instance (will also load from environment variables)
    return Config(**config_data)


def create_sample_config(config_path: Path) -> None:
    """Create a sample configuration file."""
    
    sample_config = {
        "ai": {
            "enabled": True,
            "default_provider": "anthropic",
            "openai_model": "gpt-4",
            "anthropic_model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "temperature": 0.1
        }
    }
    
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write sample config
    with open(config_path, 'w') as f:
        toml.dump(sample_config, f)
    
    print(f"Sample configuration created at: {config_path}")
    print("Please edit the file and add your API keys:")
    print("- Set OPENAI_API_KEY environment variable or add openai_api_key to config")
    print("- Set ANTHROPIC_API_KEY environment variable or add anthropic_api_key to config")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[Path] = None) -> Config:
    """Reload configuration from file."""
    global _config
    _config = load_config(config_path)
    return _config