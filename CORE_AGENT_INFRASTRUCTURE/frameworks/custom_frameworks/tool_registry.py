"""
ToolRegistry: central registry so any agent can discover and call tools
by name without hard-coding dependencies.

Tools register themselves with metadata (name, vertical, description,
permissions) — useful for LLM tool-calling and for audit logs.
"""
from typing import Any, Callable, Optional


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        vertical: Optional[str] = None,
        requires_secret: bool = False,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.vertical = vertical
        self.requires_secret = requires_secret

    def run(self, **kwargs: Any) -> Any:
        return self.func(**kwargs)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "vertical": self.vertical,
            "requires_secret": self.requires_secret,
        }


class ToolRegistry:
    """Singleton tool registry for the whole agency runtime."""

    _instance: Optional["ToolRegistry"] = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: dict[str, Tool] = {}
        return cls._instance

    def register(
        self,
        name: str,
        description: str,
        vertical: Optional[str] = None,
        requires_secret: bool = False,
    ) -> Callable:
        """Decorator to register a function as a tool."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._tools[name] = Tool(name, description, func, vertical, requires_secret)
            return func

        return decorator

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name}")
        return self._tools[name]

    def list(self, vertical: Optional[str] = None) -> list[dict]:
        tools = self._tools.values()
        if vertical:
            tools = [t for t in tools if t.vertical in (None, vertical)]
        return [t.to_dict() for t in tools]

    def execute(self, name: str, **kwargs: Any) -> Any:
        return self.get(name).run(**kwargs)


registry = ToolRegistry()
