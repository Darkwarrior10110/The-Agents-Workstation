import pytest
import os
import tempfile
import shutil
from core.cache_manager import ArtifactCache
from core.schema import Artifact, ArtifactType


class TestArtifactCache:
    @pytest.fixture
    def cache(self):
        original_dir = ArtifactCache.cache_dir if hasattr(ArtifactCache, 'cache_dir') else "storage/cache"
        test_dir = tempfile.mkdtemp()
        cache = ArtifactCache()
        cache.cache_dir = test_dir
        yield cache
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_set_and_get(self, cache):
        art = Artifact(
            task_id="task1", path="test.py",
            artifact_type=ArtifactType.FILE, content="print('hello')"
        )
        cache.set("test description", {"key": "value"}, art)

        retrieved = cache.get("test description", {"key": "value"})
        assert retrieved is not None
        assert retrieved.path == "test.py"
        assert retrieved.content == "print('hello')"
        assert retrieved.task_id == "task1"

    def test_get_miss(self, cache):
        result = cache.get("nonexistent", {})
        assert result is None

    def test_key_uniqueness(self, cache):
        art1 = Artifact(task_id="t1", path="a.py", artifact_type=ArtifactType.FILE, content="x")
        art2 = Artifact(task_id="t2", path="b.py", artifact_type=ArtifactType.FILE, content="y")

        cache.set("desc1", {"a": 1}, art1)
        cache.set("desc2", {"b": 2}, art2)

        r1 = cache.get("desc1", {"a": 1})
        r2 = cache.get("desc2", {"b": 2})
        assert r1.content == "x"
        assert r2.content == "y"

    def test_cache_persistence(self, cache):
        art = Artifact(
            task_id="task1", path="test.py",
            artifact_type=ArtifactType.FILE, content="data"
        )
        cache.set("desc", {"key": "val"}, art)

        cache2 = ArtifactCache()
        cache2.cache_dir = cache.cache_dir
        retrieved = cache2.get("desc", {"key": "val"})
        assert retrieved is not None

    def test_corrupted_cache(self, cache):
        key = cache._generate_key("desc", {})
        cache_path = os.path.join(cache.cache_dir, f"{key}.json")
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            f.write("invalid json")

        result = cache.get("desc", {})
        assert result is None

    def test_different_inputs_different_keys(self, cache):
        k1 = cache._generate_key("desc", {"a": 1})
        k2 = cache._generate_key("desc", {"a": 2})
        assert k1 != k2
