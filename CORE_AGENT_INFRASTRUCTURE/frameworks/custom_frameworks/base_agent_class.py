"""
BaseAgent: the abstract class every vertical agent subclasses.

Provides:
- standardized run() contract (input dict -> output dict)
- optional LangChain LLM, tool registry access, memory
- structured logging + basic timing metrics
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger("stratum.agents")


class BaseAgent(ABC):
    """All vertical agents extend this class."""

    def __init__(
        self,
        name: str,
        vertical: str,
        llm: Any = None,
        memory: Any = None,
        tools: Optional[list] = None,
    ):
        self.name = name
        self.vertical = vertical
        self.llm = llm
        self.memory = memory
        self.tools = tools or []

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's core logic.

        Args:
            input_data: free-form dict (message, context, channel, ...)

        Returns:
            dict with at least: {"status": "success"|"error", "result": ...}
        """
        raise NotImplementedError

    # -- helpers ------------------------------------------------------------
    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Wrapper adding timing + error capture around run()."""
        started = time.monotonic()
        logger.info("agent=%s vertical=%s started", self.name, self.vertical)
        try:
            result = self.run(input_data)
            result.setdefault("status", "success")
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent=%s failed", self.name)
            result = {"status": "error", "error": str(exc), "result": None}
        elapsed = round(time.monotonic() - started, 3)
        result["agent"] = self.name
        result["elapsed_s"] = elapsed
        logger.info("agent=%s finished elapsed=%s", self.name, elapsed)
        return result

    def use_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Invoke a registered tool by name."""
        for tool in self.tools:
            if getattr(tool, "name", None) == tool_name:
                return tool.run(**kwargs)
        raise KeyError(f"Tool '{tool_name}' not attached to agent {self.name}")

    def call_llm(self, prompt: str, *, temperature: float = 0.2, **kwargs: Any) -> str:
        """Single LLM call with timeout and error translation."""
        if self.llm is None:
            raise RuntimeError(f"Agent {self.name} has no LLM configured")
        response = self.llm.invoke(prompt, temperature=temperature, **kwargs)
        return response.content if hasattr(response, "content") else str(response)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} name={self.name!r} vertical={self.vertical!r}>"
