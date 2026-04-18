# OOTP Storyline MCP

MCP server for authoring, validating, and exporting OOTP storyline content.

Korean README: [README.ko.md](README.ko.md)

## Overview

- Author storyline projects as JSON
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

Catalog:
- `get_catalog_summary`
- `list_trigger_events`
- `get_trigger_event_details`
- `list_data_object_types`
- `list_attributes`
- `search_attributes`
- `get_attribute_details`

Projects:
- `list_projects`
- `get_project`
- `delete_project`
- `create_storyline_project`
- `bulk_create_storyline_projects`
- `update_storyline_meta`
- `remove_storyline_meta_keys`

Required data / articles:
- `add_required_data_object`
- `remove_required_data_object`
- `add_article`
- `update_article`
- `remove_article`

Validation / export:
- `validate_storyline_project`
- `bulk_validate_storyline_projects`
- `validate_storyline_bundle`
- `export_storyline_project_xml`
- `bulk_export_storyline_projects_xml`
- `export_storyline_bundle_xml`

Guidance:
- `get_authoring_guidance`

## Notes

- `projects/*.json` is not tracked by default.
- `stock/storylines_english.xml` is not tracked by default.
- This repository ships the MCP server and toolkit, not OOTP-owned content.
