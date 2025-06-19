# MCP Client Example

This example shows the *minimal* wiring needed to
use GetStream's optional **MCP** support (`getstream[mcp]`).

It does **not** implement any custom tools or resources yet –
that will be added once the `fastmcp`-based implementation lands.

## Running

```bash
uv sync -q --all-packages -p examples/mcp/pyproject.toml
uv run examples/mcp/main.py
```

Requirements: Python ≥ 3.10 and `getstream[mcp]` extra installed
(the `pyproject.toml` here declares it for you).

## What's inside?

* `main.py` – placeholder async script that will eventually
  connect to an MCP server.
* `pyproject.toml` – isolated env spec that pulls in the
  `getstream[mcp]` extra. 