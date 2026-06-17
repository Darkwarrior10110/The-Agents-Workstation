from typing import Optional, Dict, Any
from core.logger import system_logger
from core.llm_gateway import LLMGateway, ProviderFailure

class GeminiClient:
    """
    Thin wrapper around the LLMGateway. 
    Maintains backward compatibility with all existing agents so they 
    don't need to be rewritten to support multi-key resilience.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.primary_model = model_name
        self.gateway = LLMGateway.get_instance()
        self.logger = system_logger

    async def generate_content(self, prompt: str, generation_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates content from Gemini using the Gateway for automatic fallback,
        key rotation, and error handling.
        """
        return await self.gateway.generate_content(
            prompt=prompt,
            generation_config=generation_config,
            primary_model=self.primary_model
        )
