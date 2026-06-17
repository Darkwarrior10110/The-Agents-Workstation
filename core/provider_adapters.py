import httpx
from google import genai

class ProviderAdapter:
    """Base adapter for Universal LLM Gateway providers."""
    def __init__(self, api_key: str, default_model: str, fallback_models: list = None, endpoint: str = None):
        self.api_key = api_key
        self.default_model = default_model
        self.fallback_models = fallback_models or []
        self.endpoint = endpoint

    async def generate(self, prompt: str, model: str, config: dict) -> str:
        raise NotImplementedError


class GeminiAdapter(ProviderAdapter):
    """Adapter for Google Gemini using the native genai SDK."""
    def __init__(self, api_key: str, default_model: str="gemini-2.5-flash", fallback_models=None):
        super().__init__(api_key, default_model, fallback_models or ["gemini-2.5-pro", "gemini-2.0-flash"])
        self.client = genai.Client(api_key=api_key)
        
    async def generate(self, prompt: str, model: str, config: dict) -> str:
        import asyncio
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=model,
            contents=prompt,
            config=config
        )
        return response.text


class OpenAICompatibleAdapter(ProviderAdapter):
    """Adapter for GitHub Models, xAI, and other OpenAI-compatible REST endpoints."""
    async def generate(self, prompt: str, model: str, config: dict) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        # Simple REST call removes the need for managing the OpenAI SDK package versions
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload, timeout=120.0)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


class ClaudeAdapter(ProviderAdapter):
    """Adapter for Anthropic Claude REST API."""
    def __init__(self, api_key: str, default_model: str="claude-3-5-sonnet-latest", fallback_models=None):
        super().__init__(api_key, default_model, fallback_models or ["claude-3-5-haiku-latest"])
        self.endpoint = "https://api.anthropic.com/v1/messages"
        
    async def generate(self, prompt: str, model: str, config: dict) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload, timeout=120.0)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
