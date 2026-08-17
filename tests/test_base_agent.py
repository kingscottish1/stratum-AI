from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent


class OkAgent(BaseAgent):
    def run(self, input_data):
        return {"status": "success", "result": {"echo": input_data.get("x")}}


class BadAgent(BaseAgent):
    def run(self, input_data):
        raise RuntimeError("boom")


def test_execute_success():
    result = OkAgent("ok", "test").execute({"x": 1})
    assert result["status"] == "success"
    assert result["result"]["echo"] == 1
    assert "elapsed_s" in result
    assert result["agent"] == "ok"


def test_execute_captures_errors():
    result = BadAgent("bad", "test").execute({})
    assert result["status"] == "error"
    assert "boom" in result["error"]


def test_use_tool_unknown():
    agent = OkAgent("ok", "test")
    try:
        agent.use_tool("nope")
        raised = False
    except KeyError:
        raised = True
    assert raised
