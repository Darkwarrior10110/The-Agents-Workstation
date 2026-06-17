import hashlib
import json
import os
from typing import Optional
from core.schema import Artifact
from core.logger import system_logger

class ArtifactCache:
    def __init__(self):
        self.cache_dir = "storage/cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _generate_key(self, task_description: str, input_data: dict) -> str:
        # Create a deterministic key based on the goal task description and input parameters
        # Sorting keys ensures consistent hashing
        data_str = json.dumps(input_data, sort_keys=True, default=str)
        combined = f"{task_description}_{data_str}".encode('utf-8')
        return hashlib.sha256(combined).hexdigest()
        
    def get(self, task_description: str, input_data: dict) -> Optional[Artifact]:
        key = self._generate_key(task_description, input_data)
        path = os.path.join(self.cache_dir, f"{key}.json")
        
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    system_logger.info(f"[CACHE] Cache hit for artifact key: {key}")
                    return Artifact(**data)
            except Exception as e:
                system_logger.warning(f"[CACHE] Failed to read cache: {str(e)}")
        
        return None
        
    def set(self, task_description: str, input_data: dict, artifact: Artifact):
        key = self._generate_key(task_description, input_data)
        path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(path, "w") as f:
                json.dump(artifact.dict(), f, default=str)
            system_logger.info(f"[CACHE] Saved artifact to cache: {key}")
        except Exception as e:
            system_logger.warning(f"[CACHE] Failed to write cache: {str(e)}")
