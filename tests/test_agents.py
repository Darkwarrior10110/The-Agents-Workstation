import pytest
from agents.base_agent import BaseAgent, AgentResponse
from core.schema import Task, TaskStatus


class TestAgentResponse:
    def test_minimal_creation(self):
        resp = AgentResponse(
            agent_name="test-agent",
            status=TaskStatus.COMPLETED,
            output={"result": "ok"}
        )
        assert resp.agent_name == "test-agent"
        assert resp.status == TaskStatus.COMPLETED
        assert resp.output == {"result": "ok"}
        assert resp.logs == []
        assert resp.metadata == {}

    def test_with_logs_and_metadata(self):
        resp = AgentResponse(
            agent_name="test-agent",
            status=TaskStatus.FAILED,
            output={"error": "fail"},
            logs=["error occurred"],
            metadata={"attempt": 1}
        )
        assert len(resp.logs) == 1
        assert resp.metadata["attempt"] == 1


class ConcreteAgent(BaseAgent):
    def __init__(self, name="TestAgent", role="Tester"):
        super().__init__(name, role)

    async def execute(self, task, context=None):
        return AgentResponse(
            agent_name=self.name,
            status=TaskStatus.COMPLETED,
            output={"task": task.description}
        )


class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_execute_returns_response(self):
        agent = ConcreteAgent()
        task = Task(goal_id="g1", agent_type="test", task_type="test", description="test task")
        response = await agent.execute(task)
        assert response.agent_name == "TestAgent"
        assert response.status == TaskStatus.COMPLETED

    def test_repr(self):
        agent = ConcreteAgent()
        assert "TestAgent" in repr(agent)
        assert "Tester" in repr(agent)

    def test_log_method(self, mocker):
        agent = ConcreteAgent()
        mock_logger = mocker.patch.object(agent.logger, "info")
        agent.log("test message")
        mock_logger.assert_called_once_with("test message")
