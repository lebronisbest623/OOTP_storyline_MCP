# OOTP Storyline MCP

A small MCP server and toolkit for building, validating, and exporting OOTP storyline content.

## Current scope

- Extract a catalog of stock storyline attributes, triggers, and object types from OOTP 27.
- Merge in engine-discovered trigger events surfaced by OOTP debug reports, even when stock XML does not use them directly.
- Expose that catalog through MCP tools so an LLM can inspect the supported schema safely.
- Provide a JSON schema starter for authored storyline projects.
- Store authored storyline projects as JSON in `projects/`.
- Validate authored projects against the local schema plus the stock attribute catalog and engine-discovered trigger inventory.
- Export authored projects as OOTP-style XML into `exports/`.
- Support bulk project creation, bulk validation, per-project export, and bundled multi-storyline XML export.

## Layout

- `src/ootp_storyline_mcp/`: MCP server and catalog loader
- `scripts/`: helper scripts
- `catalog/`: generated catalog JSON files
- `schemas/`: JSON schema for authored storylines
- `projects/`: user-authored storyline projects
- `exports/`: generated XML outputs
- `stock/`: optional local sidecar copies of reference OOTP files

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

## Authoring flow

1. Create a new project with `create_storyline_project`
2. Add actor filters with `add_required_data_object`
3. Add or edit article blocks with `add_article` / `update_article`
4. Remove bad keys or blocks with `remove_storyline_meta_keys`, `remove_required_data_object`, or `remove_article`
5. Run `validate_storyline_project` or `bulk_validate_storyline_projects`
6. Run `validate_storyline_bundle` before final multi-project export
7. Export XML with `export_storyline_project_xml` or build one combined file with `export_storyline_bundle_xml`

## Current sample output

- Project JSON: `projects/kbo_test_rookie_v2.json`
- Export XML: `exports/kbo_test_rookie_v2.xml`
- Bundled export target: `exports/storyline_bundle.xml`

## Notes

- Root storyline attributes are intentionally permissive at the schema layer so stock attributes such as `league_nation_id` are not blocked before catalog validation runs.
- Section names for `list_attributes` and `get_attribute_details` are normalized case-insensitively. `STORYLINE`, `root`, `required_data`, `articles`, and similar aliases are accepted.
- `list_trigger_events` can now surface both `stock_xml` triggers and `engine_debug_trace` triggers. Use `get_trigger_event_details` if you need to see where a trigger came from.
- For large authoring batches, prefer many small projects plus one bundle export instead of continually growing one giant project.
- Bundle validation checks cross-project article id collisions before export.
- The server reloads local catalog, validation, export, and project-store modules on each tool call, so edits to those modules should be reflected without a full server restart in most cases.
- PowerShell can render some UTF-8 Korean text poorly; trust the saved UTF-8 project and export files over raw terminal output when checking final text.

## Quick start

```powershell
cd C:\Users\user\OOTP_storyline_MCP
python scripts\extract_storyline_catalog.py
python run_server.py
```

## Stock source

Catalog extraction resolves the stock XML in this order:

1. `OOTP_STORYLINE_SOURCE_XML` environment variable
2. local sidecar copy at `stock/storylines_english.xml`
3. installed OOTP default path

This keeps the MCP portable without requiring a hardcoded install path in normal workflow, while avoiding bundling game-owned files by default.
