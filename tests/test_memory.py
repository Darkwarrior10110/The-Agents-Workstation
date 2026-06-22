import pytest
from core.memory import SharedMemory


class TestSharedMemory:
    @pytest.fixture
    def memory(self):
        return SharedMemory()

    def test_initial_state(self, memory):
        ctx = memory.get_context()
        assert ctx["failures"] == {}
        assert ctx["repairs"] == []
        assert ctx["failed_patches"] == {}
        assert ctx["generated_files"] == []

    def test_record_failure(self, memory):
        memory.record_failure("backend", "test.py")
        ctx = memory.get_context()
        assert "backend" in ctx["failures"]
        assert ctx["failures"]["backend"]["count"] == 1

    def test_record_multiple_failures(self, memory):
        memory.record_failure("backend", "a.py")
        memory.record_failure("backend", "b.py")
        ctx = memory.get_context()
        assert ctx["failures"]["backend"]["count"] == 2

    def test_record_repair(self, memory):
        memory.record_repair("task1", "Fixed backend", True)
        ctx = memory.get_context()
        assert len(ctx["repairs"]) == 1
        assert ctx["repairs"][0]["task_id"] == "task1"

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
        assert len(ctx["generated_files"]) == 1
        assert ctx["generated_files"][0]["path"] == "test.py"
