"""CLI adapter for the CodeStrata FastMCP server."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer

from aimf.config import load_settings
from aimf.interfaces.mcp.factory import create_mcp_server
from aimf.logging_config import configure_logging

mcp_app = typer.Typer(
    name="mcp",
    help="CodeStrata Model Context Protocol (MCP) server commands.",
    no_args_is_help=True,
)


@mcp_app.command("serve")
def serve(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to aimf.toml.",
        ),
    ] = Path("aimf.toml"),
    log_level: Annotated[
        str | None,
        typer.Option(
            "--log-level",
            help="Override MCP log level (default from [mcp].log_level).",
        ),
    ] = None,
) -> None:
    """Start the CodeStrata FastMCP server on stdio.

    Logs are written to stderr so the MCP protocol on stdout stays clean.
    """

    try:
        settings = load_settings(config)
    except (FileNotFoundError, ValueError, OSError) as error:
        # Startup failures before protocol handshake may use stderr.
        print(f"CodeStrata MCP failed to load configuration: {error}", file=sys.stderr)
        raise typer.Exit(code=1) from error

    if not settings.mcp.enabled:
        print("CodeStrata MCP is disabled in configuration ([mcp].enabled=false).", file=sys.stderr)
        raise typer.Exit(code=1)

    resolved_level = (log_level or settings.mcp.log_level).upper()
    configure_logging(level=resolved_level)
    # Ensure handlers write to stderr for stdio transport safety.
    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setStream(sys.stderr)

    logger = logging.getLogger("aimf.interfaces.mcp")
    try:
        server = create_mcp_server(settings=settings, config_path=config)
    except Exception as error:  # noqa: BLE001 - CLI boundary
        logger.exception("mcp_server_composition_failed")
        print(f"CodeStrata MCP failed to start: {error}", file=sys.stderr)
        raise typer.Exit(code=1) from error

    logger.info("Starting CodeStrata MCP server transport=%s", settings.mcp.transport)
    server.run(transport="stdio")
