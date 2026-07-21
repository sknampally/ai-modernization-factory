"""Registry for provider-neutral AIMF tools."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel

from aimf.ai.tools.base import (
    AIMFTool,
    AIMFToolError,
    AIMFToolExecutionError,
    AIMFToolInputError,
)
from aimf.ai.tools.models import AIMFToolDefinition, AIMFToolResult


class AIMFToolRegistry:
    """Register, discover, and execute typed AIMF tools."""

    def __init__(self) -> None:
        self._tools: dict[str, AIMFTool[Any, Any]] = {}

    def register(self, tool: AIMFTool[Any, Any]) -> None:
        """Register a tool. Duplicate names are rejected case-insensitively."""

        key = tool.name.strip().lower()
        if not key:
            raise ValueError("Tool name must be a nonempty string")
        if key in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[key] = tool

    def register_many(self, tools: Iterable[AIMFTool[Any, Any]]) -> None:
        """Register multiple tools atomically for the provided iterable order."""

        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> AIMFTool[Any, Any]:
        """Retrieve a tool by name using case-insensitive lookup."""

        key = name.strip().lower()
        try:
            return self._tools[key]
        except KeyError as error:
            raise KeyError(f"Unknown tool: {name}") from error

    def has(self, name: str) -> bool:
        """Return whether a tool is registered."""

        return name.strip().lower() in self._tools

    def list_definitions(self) -> list[AIMFToolDefinition]:
        """Return tool definitions in stable name order."""

        tools = sorted(self._tools.values(), key=lambda tool: tool.name.lower())
        return [tool.definition() for tool in tools]

    def list_names(self) -> list[str]:
        """Return registered tool names in stable order."""

        return [item.name for item in self.list_definitions()]

    def execute(
        self,
        name: str,
        payload: BaseModel | Mapping[str, object] | None = None,
    ) -> AIMFToolResult:
        """Execute a tool and always return an AIMFToolResult."""

        normalized_name = name.strip() if name else ""
        try:
            tool = self.get(normalized_name)
        except KeyError:
            return AIMFToolResult(
                tool_name=normalized_name or name,
                success=False,
                data=None,
                error=f"Unknown tool: {name}",
            )

        try:
            output = tool.execute(dict(payload) if isinstance(payload, Mapping) else payload)
            return AIMFToolResult(
                tool_name=tool.name,
                success=True,
                data=output.model_dump(mode="json"),
                error=None,
            )
        except AIMFToolInputError as error:
            return AIMFToolResult(
                tool_name=tool.name,
                success=False,
                data=None,
                error=str(error),
            )
        except AIMFToolExecutionError as error:
            return AIMFToolResult(
                tool_name=tool.name,
                success=False,
                data=None,
                error=str(error),
            )
        except AIMFToolError as error:
            return AIMFToolResult(
                tool_name=tool.name,
                success=False,
                data=None,
                error=str(error),
            )
        except Exception:  # noqa: BLE001 - hard boundary
            return AIMFToolResult(
                tool_name=tool.name,
                success=False,
                data=None,
                error=f"Tool '{tool.name}' failed during execution.",
            )
