# OOTP Storyline MCP

An MCP server for authoring, validating, and exporting OOTP storyline content as structured JSON projects and OOTP-compatible XML.

Korean README: [README.ko.md](README.ko.md)

## What this repository is for

This repository is focused on the **server and authoring toolkit itself**.

It is designed for users who want to connect an MCP-capable coding agent to a local OOTP storyline workflow, inspect the supported schema safely, validate storyline projects, and export final XML files.

## Features

- Browse storyline attributes, trigger events, and data object types through MCP tools
- Author storyline projects as JSON
- Validate single projects and multi-project bundles
- Export OOTP-style XML for one project or many projects
- Surface both:
  - `stock_xml` triggers discovered from stock storyline XML
  - `engine_debug_trace` triggers discovered from OOTP debug traces

## Repository layout

- `src/ootp_storyline_mcp/`: MCP server implementation
- `catalog/`: generated catalog JSON
- `schemas/`: authored storyline JSON schema
- `projects/`: local authored project folder
- `exports/`: generated XML outputs
- `stock/`: optional local sidecar copy of stock OOTP storyline XML

## Quick start

```powershell
cd C:\Users\user\OOTP_storyline_MCP
python run_server.py
```

## Connect from Codex

Codex reads MCP server configuration from `~/.codex/config.toml`.

Add a server entry like this:

```toml
[mcp_servers.ootp_storyline]
command = "python"
args = ["C:\\Users\\user\\OOTP_storyline_MCP\\run_server.py"]
enabled = true
```

After saving the file, restart Codex or refresh the session so the new server is loaded.

## Connect from Claude Code

Claude Code supports project-scoped MCP configuration through `.mcp.json`, or you can add a server from the CLI.

### Option 1: add it from the CLI

From the repository root:

```powershell
claude mcp add --scope project ootp-storyline -- python run_server.py
```

Then confirm it is available:

```powershell
claude mcp list
```

Inside Claude Code, you can also inspect MCP status with:

```text
/mcp
```

### Option 2: create a project `.mcp.json`

Create `.mcp.json` in the repository root:

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

This is the best option when you want the server configuration checked into a project-level workflow.

## Connect from Cursor

Cursor supports MCP via `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` globally.

Create `.cursor/mcp.json` in the repository root:

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

Then restart Cursor or reload the workspace so the MCP server is picked up.

## Current MCP tools

- `get_catalog_summary`
- `list_trigger_events`
- `get_trigger_event_details`
- `list_data_object_types`
- `list_attributes`
- `search_attributes`
- `get_attribute_details`
- `list_projects`
- `get_project`
- `delete_project`
- `create_storyline_project`
- `bulk_create_storyline_projects`
- `update_storyline_meta`
- `remove_storyline_meta_keys`
- `add_required_data_object`
- `remove_required_data_object`
- `add_article`
- `update_article`
- `remove_article`
- `validate_storyline_project`
- `bulk_validate_storyline_projects`
- `validate_storyline_bundle`
- `export_storyline_project_xml`
- `bulk_export_storyline_projects_xml`
- `export_storyline_bundle_xml`
- `get_authoring_guidance`

## Recommended authoring workflow

1. Create one project per event with `create_storyline_project`
2. Add actor filters with `add_required_data_object`
3. Add or edit article blocks with `add_article` / `update_article`
4. Remove bad keys with `remove_storyline_meta_keys`, `remove_required_data_object`, or `remove_article`
5. Run `validate_storyline_project` or `bulk_validate_storyline_projects`
6. Before exporting many projects together, run `validate_storyline_bundle`
7. Export with `export_storyline_project_xml` or `export_storyline_bundle_xml`

For large content batches, many small projects plus one bundle XML is safer than growing one giant project.

## Trigger source notes

`list_trigger_events` can include two kinds of triggers:

- `stock_xml`: found directly in stock OOTP storyline XML
- `engine_debug_trace`: found from OOTP debug trace output even when stock XML does not use them directly

Use `get_trigger_event_details` if you want to see where a trigger came from.

## Stock XML resolution order

The catalog loader resolves the stock XML in this order:

1. `OOTP_STORYLINE_SOURCE_XML` environment variable
2. local sidecar file at `stock/storylines_english.xml`
3. default installed OOTP path

This keeps the MCP server portable without requiring a hardcoded install path in the normal workflow.

## Public repository rules

- `projects/*.json` is intentionally not tracked by default
- `stock/storylines_english.xml` is intentionally not tracked by default
- This repository is for the MCP server and toolkit, not for redistributing OOTP-owned content
