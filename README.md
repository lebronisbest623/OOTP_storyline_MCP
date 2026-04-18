# OOTP Storyline MCP

MCP server for editing OOTP storylines as local JSON files and compiling them back into a single OOTP-compatible XML file.

Korean README: [README.ko.md](README.ko.md)

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

## Storage model

- `projects/*.json`: one storyline per file
- `projects/_workspace.json`: local source XML metadata
- `projects/_article_ids.json`: stable compiled `ARTICLE id` assignments
- `save_workspace_xml`: compiles every project file into one XML file

## Recommended workflow

1. `import_storyline_xml`
2. `get_workspace`
3. `get_project`
4. `patch_storyline_project`
5. `validate_storyline_project` or `validate_workspace`
6. `save_workspace_xml`

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

Global `~/.mcp.json`:

```json
{
  "mcpServers": {
    "ootp-storyline": {
      "type": "stdio",
      "command": "python",
      "args": ["C:\\Users\\<user>\\OOTP_storyline_MCP\\run_server.py"],
      "env": {}
    }
  }
}
```

Use an absolute path in global config.

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

Use an absolute path if you configure Cursor globally instead of per project.

## Core tools

Catalog:
- `get_catalog_summary`
- `list_trigger_events`
- `list_data_object_types`
- `list_attributes`

Workspace:
- `get_workspace`
- `import_storyline_xml`
- `save_workspace_xml`

Storylines:
- `get_project`
- `delete_project`
- `create_storyline_project`
- `patch_storyline_project`

Validation:
- `validate_storyline_project`
- `validate_workspace`

Guidance:
- `get_authoring_guidance`
