import os
import time
import asyncio
from typing import Optional, Dict, Any, List
from core.logger import system_logger
from core.provider_adapters import ProviderAdapter, GeminiAdapter, OpenAICompatibleAdapter, ClaudeAdapter
from dotenv import load_dotenv

load_dotenv()

class ProviderFailure(Exception):
    pass

class KeyStatus:
    HEALTHY = "healthy"
    COOLDOWN = "cooldown"
    INVALID = "invalid"

class ProviderKey:
    def __init__(self, adapter: ProviderAdapter, index: int, provider_name: str, priority: int):
        self.adapter = adapter
        self.index = index
        self.provider_name = provider_name
        self.priority = priority
        self.status = KeyStatus.HEALTHY
        self.cooldown_until = 0.0
        self.success_count = 0
        self.consecutive_failures = 0
        self.last_success_time = 0.0
        self.last_error = ""
        self.last_model = ""

class LLMGateway:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.logger = system_logger
        self.keys: List[ProviderKey] = []
        self._load_keys()
        
    def _load_keys(self):
        """Loads API keys from environment variables and configures providers."""
        idx = 1
        
        # 1. Gemini (Priority 1)
        gemini_keys = []
        multi_keys = os.getenv("GEMINI_API_KEYS")
        if multi_keys:
            gemini_keys.extend([k.strip() for k in multi_keys.split(",") if k.strip()])
            
        primary = os.getenv("GEMINI_API_KEY")
        if primary and primary not in gemini_keys:
            gemini_keys.append(primary)
            
        i = 2
        while True:
            k = os.getenv(f"GEMINI_API_KEY_{i}")
            if not k:
                break
            if k not in gemini_keys:
                gemini_keys.append(k)
            i += 1
            
        for k in gemini_keys:
            self.keys.append(ProviderKey(GeminiAdapter(k), idx, "Gemini", 1))
            idx += 1
            
        # 2. GitHub Models (Priority 2)
        gh_token = os.getenv("GITHUB_MODELS_TOKEN")
        if gh_token:
            gh_endpoint = os.getenv("GITHUB_MODELS_ENDPOINT", "https://models.inference.ai.azure.com/chat/completions")
            gh_model = os.getenv("GITHUB_MODELS_MODEL", "gpt-4o")
            self.keys.append(ProviderKey(OpenAICompatibleAdapter(gh_token, gh_model, endpoint=gh_endpoint), idx, "GitHub Models", 2))
            idx += 1
            
        # 3. xAI (Priority 3)
        xai_key = os.getenv("XAI_API_KEY")
        if xai_key:
            xai_model = os.getenv("XAI_MODEL", "grok-beta")
            self.keys.append(ProviderKey(OpenAICompatibleAdapter(xai_key, xai_model, endpoint="https://api.x.ai/v1/chat/completions"), idx, "xAI", 3))
            idx += 1
            
        # 4. Claude (Priority 4)
        claude_key = os.getenv("CLAUDE_API_KEY")
        if claude_key:
            claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
            self.keys.append(ProviderKey(ClaudeAdapter(claude_key, claude_model), idx, "Claude", 4))
            idx += 1

        if not self.keys:
            self.logger.error("[LLM-GATEWAY] No API keys found for any provider.")
            raise ValueError("At least one provider API key is required.")
            
        # Log loaded providers
        providers_loaded = set(k.provider_name for k in self.keys)
        self.logger.info(f"[LLM-GATEWAY] Initialized with {len(self.keys)} total keys across providers: {', '.join(providers_loaded)}.")

    def _get_best_key(self) -> Optional[ProviderKey]:
        now = time.time()
        
        # 1. Restore cooled down keys
        for pk in self.keys:
            if pk.status == KeyStatus.COOLDOWN and now >= pk.cooldown_until:
                self.logger.info(f"[LLM-GATEWAY] Cooldown expired. {pk.provider_name} #{pk.index} restored to candidate pool.")
                pk.status = KeyStatus.HEALTHY
                pk.consecutive_failures = 0
                
        # 2. Filter healthy keys
        healthy_keys = [k for k in self.keys if k.status == KeyStatus.HEALTHY]
        
        if not healthy_keys:
            return None
            
        # 3. Prioritize: Lowest Priority number first (1=Best), then highest success count, then fewest failures
        healthy_keys.sort(key=lambda k: (k.priority, -k.success_count, k.consecutive_failures, k.index))
        return healthy_keys[0]

    def _clean_response(self, text: str) -> str:
        """Strips markdown formatting to ensure pure JSON is returned to the agents."""
        if not text:
            return ""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    async def generate_content(self, prompt: str, generation_config: Optional[Dict[str, Any]] = None, primary_model: Optional[str] = None) -> str:
        config = generation_config or {"response_mime_type": "application/json"}
        last_global_error = None
        
        while True:
            pk = self._get_best_key()
            
            # Intelligent Recovery Strategy
            if not pk:
                cooling_keys = [k for k in self.keys if k.status == KeyStatus.COOLDOWN]
                if cooling_keys:
                    cooling_keys.sort(key=lambda k: k.cooldown_until)
                    earliest = cooling_keys[0]
                    sleep_time = earliest.cooldown_until - time.time()
                    if sleep_time > 0:
                        self.logger.warning(f"[LLM-GATEWAY] All providers exhausted. Next provider recovery in {sleep_time:.1f}s. Waiting...")
                        await asyncio.sleep(sleep_time)
                    continue # Re-evaluate best key after sleep
                else:
                    error_msg = f"All API keys are permanently invalid. Last error: {str(last_global_error)}"
                    self.logger.error(f"[LLM-GATEWAY] {error_msg}")
                    raise ProviderFailure(error_msg)
            
            # Setup models sequence based on adapter
            models = [pk.adapter.default_model] + pk.adapter.fallback_models
            
            # If the original client requested a specific primary_model (e.g. gemini-2.5-flash)
            # and the active adapter is Gemini, respect the request.
            if isinstance(pk.adapter, GeminiAdapter) and primary_model and primary_model not in models:
                models.insert(0, primary_model)

            self.logger.info(f"[LLM-GATEWAY] Active Provider: {pk.provider_name} (Priority {pk.priority}) using model {models[0]}")
            
            try:
                from core.runtime_state import state_manager
                state_manager.push_event("llm_status", {"active_provider": pk.provider_name, "active_model": models[0], "key_index": pk.index})
            except ImportError:
                pass
            
            key_failed_recoverably = False
            
            for model in models:
                try:
                    if model != models[0]:
                        self.logger.warning(f"[LLM-GATEWAY] Trying alternate model: {model} on {pk.provider_name}")
                        try:
                            from core.runtime_state import state_manager
                            state_manager.push_event("llm_status", {"active_provider": pk.provider_name, "active_model": model, "key_index": pk.index})
                        except ImportError:
                            pass
                        
                    response_text = await pk.adapter.generate(prompt, model, config)
                    response_text = self._clean_response(response_text)
                    
                    # Success State Update
                    pk.success_count += 1
                    pk.consecutive_failures = 0
                    pk.last_success_time = time.time()
                    pk.last_model = model
                    
                    try:
                        from core.runtime_state import state_manager
                        state_manager.push_event("increment_telemetry", {"key": "llm_requests"})
                    except ImportError:
                        pass
                        
                    return response_text
                    
                except Exception as e:
                    error_str = str(e).lower()
                    last_global_error = e
                    self.logger.warning(f"[LLM-GATEWAY] Error on {pk.provider_name} #{pk.index}, model {model}: {str(e)}")
                    pk.last_error = str(e)
                    
                    # Universal Error Classification
                    recoverable_indicators = [
                        "429", "quota", "resource_exhausted", "503", "404", "not_found", 
                        "timeout", "overloaded", "internal server error", "500", "502", "504",
                        "too many requests", "rate limit"
                    ]
                    
                    if any(err in error_str for err in recoverable_indicators):
                        key_failed_recoverably = True
                        continue # Try next model
                    else:
                        # Non-recoverable (e.g. 400 Bad Request, 401 Unauthorized, invalid key format)
                        self.logger.error(f"[LLM-GATEWAY] Non-recoverable error on {pk.provider_name} #{pk.index}. Marking as invalid.")
                        pk.status = KeyStatus.INVALID
                        pk.consecutive_failures += 1
                        key_failed_recoverably = False
                        break # Break model loop, try next key

            if pk.status == KeyStatus.INVALID:
                self.logger.info(f"[LLM-GATEWAY] {pk.provider_name} unavailable, failing over to next provider.")
                continue # Loop back to find a new key
                
            if key_failed_recoverably:
                pk.consecutive_failures += 1
                # Exponential backoff: 60s, 120s, 240s...
                cooldown_time = 60 * (2 ** (pk.consecutive_failures - 1))
                if cooldown_time > 600:
                    cooldown_time = 600
                    
                pk.status = KeyStatus.COOLDOWN
                pk.cooldown_until = time.time() + cooldown_time
                self.logger.warning(f"[LLM-GATEWAY] All models failed for {pk.provider_name} #{pk.index}. Entering {cooldown_time}s cooldown.")
                self.logger.info(f"[LLM-GATEWAY] {pk.provider_name} unavailable, failing over to next provider.")
                continue # Try next key
