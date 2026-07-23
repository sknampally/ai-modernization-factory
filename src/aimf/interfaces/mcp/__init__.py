"""CodeStrata FastMCP adapter over application services.

This package is a thin transport layer. Business logic remains in
``AssessmentApplicationService`` and ``KnowledgeQueryService``.
"""

from aimf.interfaces.mcp.factory import create_mcp_server
from aimf.interfaces.mcp.server import CODESSTRATA_MCP_NAME, build_mcp_server

__all__ = [
    "CODESSTRATA_MCP_NAME",
    "build_mcp_server",
    "create_mcp_server",
]
