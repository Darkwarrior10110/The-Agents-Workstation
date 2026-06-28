import pytest
from core.memory import SharedMemory


class TestSharedMemory:
    @pytest.fixture
    def memory(self):
        return SharedMemory()

    def test_initial_state(self, memory):
        ctx = memory.get_context()
        assert ctx["project_map"] is not None
        assert ctx["generated_files"] == {}
        assert ctx["recent_repairs"] == []
        assert ctx["unstable_agents"] == {}
        assert ctx["unstable_files"] == {}
        assert ctx["failed_patches"] == {}

    def test_record_failure(self, memory):
        memory.record_failure("backend", "test.py")
        ctx = memory.get_context()
        assert ctx["unstable_agents"]["backend"] == 1
        assert ctx["unstable_files"]["test.py"] == 1

    def test_record_multiple_failures(self, memory):
        memory.record_failure("backend", "a.py")
        memory.record_failure("backend", "b.py")
        ctx = memory.get_context()
        assert ctx["unstable_agents"]["backend"] == 2
        assert ctx["unstable_files"]["a.py"] == 1
        assert ctx["unstable_files"]["b.py"] == 1

    def test_record_repair(self, memory):
        memory.record_repair("task1", "Fixed backend", True)
        ctx = memory.get_context()
        assert len(ctx["recent_repairs"]) == 1
        assert ctx["recent_repairs"][0]["task_id"] == "task1"

    def test_record_failed_patch(self, memory):
        memory.record_failed_patch("test.py", "old_code", "new_code")
        ctx = memory.get_context()
        assert "test.py" in ctx["failed_patches"]
        assert len(ctx["failed_patches"]["test.py"]) == 1

    def test_record_failed_patch_with_reason(self, memory):
        memory.record_failed_patch("test.py", "old", "new", reason="syntax error")
        ctx = memory.get_context()
        assert ctx["failed_patches"]["test.py"][0]["reason"] == "syntax error"

    def test_add_generated_file(self, memory):
        memory.add_generated_file("test.py", "A test file")
        ctx = memory.get_context()
        assert "test.py" in ctx["generated_files"]
        assert ctx["generated_files"]["test.py"] == "A test file"

    def test_limit_recent_repairs(self, memory):
        for i in range(10):
            memory.record_repair(f"task{i}", f"fix{i}", True)
        ctx = memory.get_context()
        assert len(ctx["recent_repairs"]) == 5

    def test_update_map(self, memory):
        memory.update_map({"routes": ["/api/health"], "components": ["Header"]})
        ctx = memory.get_context()
        assert "/api/health" in ctx["project_map"]["routes"]
        assert "Header" in ctx["project_map"]["components"]
