from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.tool_registry import ToolRegistry


def _fresh_registry():
    ToolRegistry._instance = None
    return ToolRegistry()


def test_register_and_execute():
    registry = _fresh_registry()

    @registry.register("double", "Multiply by two")
    def double(x):
        return x * 2

    assert registry.get("double").name == "double"
    assert registry.execute("double", x=21) == 42
    assert registry.list() == [{"name": "double", "description": "Multiply by two",
                                "vertical": None, "requires_secret": False}]


def test_unknown_tool_raises():
    registry = _fresh_registry()
    try:
        registry.get("missing")
        raised = False
    except KeyError:
        raised = True
    assert raised
