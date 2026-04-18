# OOTP Storyline MCP

MCP server for authoring, validating, and exporting OOTP storyline content.

Korean README: [README.ko.md](README.ko.md)

## Overview

- Store authored storyline entries in one accumulated workspace JSON file
- Validate single projects and multi-project bundles
- Export OOTP-compatible XML
- Support triggers discovered from both stock XML and engine debug traces

## Requirements

- Python 3
- OOTP storyline source XML available through one of:
  1. `OOTP_STORYLINE_SOURCE_XML`
  2. `stock/storylines_english.xml`
  3. default installed OOTP path

## Run

```powershell
cd C:\Users\user\OOTP_storyline_MCP
python run_server.py
```

## Client setup

### Codex

Add this to `~/.codex/config.toml`:

```toml
[mcp_servers.ootp_storyline]
command = "python"
args = ["C:\\Users\\user\\OOTP_storyline_MCP\\run_server.py"]
enabled = true
```

### Claude Code

CLI setup:

```powershell
claude mcp add --scope project ootp-storyline -- python run_server.py
```

Project `.mcp.json`:

```json
{
  "mcpServers": {
    "ootp-storyline": {
      "command": "python",
      "args": ["run_server.py"],
      "env": {}
    }
  }
}
```

### Cursor

Project `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ootp-storyline": {
      "command": "python",
      "args": ["${workspaceFolder}/run_server.py"],
      "env": {}
    }
  }
}
```

## Core tools

Workspace:
- `get_workspace`
- `import_storyline_xml`
- `save_workspace_xml`

Catalog:
- `get_catalog_summary`
- `list_trigger_events`
- `list_data_object_types`
- `list_attributes`

Storyline entries:
- `get_project`
- `delete_project`
- `create_storyline_project`
- `patch_storyline_project`

Validation / export:
- `validate_storyline_project`
- `validate_workspace`

Guidance:
- `get_authoring_guidance`

## Notes

- The default authoring target is `projects/storyline_workspace.json`.
- `projects/*.json` is not tracked by default.
- `stock/storylines_english.xml` is not tracked by default.
- This repository ships the MCP server and toolkit, not OOTP-owned content.
