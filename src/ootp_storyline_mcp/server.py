import importlib
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import catalog as catalog_module
from . import project_store as project_store_module
from . import validation as validation_module
from . import xml_export as xml_export_module
from . import xml_import as xml_import_module

mcp = FastMCP("OOTP Storyline MCP")


SECTION_ALIASES = {
    "storyline": "storyline",
    "storylines": "storyline",
    "root": "storyline",
    "meta": "storyline",
    "data_object": "data_object",
    "dataobject": "data_object",
    "required_data": "data_object",
    "required-data": "data_object",
    "article": "article",
    "articles": "article",
}


def _catalog() -> dict[str, Any]:
    runtime = _runtime()
    return runtime["catalog"].load_catalog(runtime["catalog"].DEFAULT_CATALOG_PATH).data


def _runtime() -> dict[str, Any]:
    importlib.reload(catalog_module)
    importlib.reload(project_store_module)
    importlib.reload(validation_module)
    importlib.reload(xml_export_module)
    importlib.reload(xml_import_module)
    return {
        "catalog": catalog_module,
        "project_store": project_store_module,
        "validation": validation_module,
        "xml_export": xml_export_module,
        "xml_import": xml_import_module,
    }



def _normalize_section(section: str) -> str:
    normalized = section.strip().lower()
    normalized = normalized.replace(" ", "_")
    if normalized not in SECTION_ALIASES:
        raise ValueError(
            "section must be one of: storyline/root, data_object/required_data, article/articles"
        )
    return SECTION_ALIASES[normalized]



def _project_with_validation(project: dict[str, Any]) -> dict[str, Any]:
    runtime = _runtime()
    return {
        "project": project,
        "validation": runtime["validation"].validate_project(project),
    }


@mcp.tool()
def get_catalog_summary() -> dict[str, Any]:
    data = _catalog()
    trigger_sources = [set(record.get("sources", [])) for record in data["trigger_events"]]
    return {
        "source_path": data["source_path"],
        "storyline_count": data["storyline_count"],
        "data_object_count": data["data_object_count"],
        "article_count": data["article_count"],
        "trigger_event_count": len(data["trigger_events"]),
        "stock_trigger_event_count": sum(1 for sources in trigger_sources if "stock_xml" in sources),
        "engine_only_trigger_event_count": sum(
            1 for sources in trigger_sources if sources == {"engine_debug_trace"}
        ),
        "data_object_type_count": len(data["data_object_types"]),
        "storyline_attribute_count": len(data["storyline_attributes"]),
        "data_object_attribute_count": len(data["data_object_attributes"]),
        "article_attribute_count": len(data["article_attributes"]),
    }


@mcp.tool()
def list_trigger_events(source: str = "", query: str = "") -> list[dict[str, Any]]:
    records = _catalog()["trigger_events"]
    source_filter = source.strip().lower().replace("-", "_")
    if not source_filter:
        filtered = records
    else:
        filtered = [record for record in records if source_filter in record.get("sources", [])]
    query_lower = query.strip().lower()
    if not query_lower:
        return filtered
    return [record for record in filtered if query_lower in record["name"].lower()]


@mcp.tool()
def list_data_object_types() -> list[dict[str, Any]]:
    return _catalog()["data_object_types"]


@mcp.tool()
def list_attributes(section: str = "", query: str = "") -> list[dict[str, Any]]:
    data = _catalog()
    mapping = {
        "storyline": data["storyline_attributes"],
        "data_object": data["data_object_attributes"],
        "article": data["article_attributes"],
    }
    sections = ["storyline", "data_object", "article"]
    if section.strip():
        sections = [_normalize_section(section)]

    query_lower = query.strip().lower()
    results: list[dict[str, Any]] = []
    for current_section in sections:
        for record in mapping[current_section]:
            if query_lower:
                haystacks = [record["name"].lower(), *(sample.lower() for sample in record.get("samples", []))]
                if not any(query_lower in hay for hay in haystacks):
                    continue
            results.append({"section": current_section, **record})
    return results


@mcp.tool()
def get_workspace() -> dict[str, Any]:
    runtime = _runtime()
    workspace = runtime["project_store"].load_workspace()
    return {
        "workspace": runtime["project_store"].get_workspace_summary(),
        "storylines": runtime["project_store"].list_projects(),
        "validation": runtime["validation"].validate_bundle(workspace.get("storylines", [])),
    }


@mcp.tool()
def import_storyline_xml(xml_path: str, mode: str = "replace") -> dict[str, Any]:
    runtime = _runtime()
    parsed = runtime["xml_import"].parse_storyline_xml(xml_path)
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"replace", "append"}:
        raise ValueError("mode must be 'replace' or 'append'")

    if normalized_mode == "replace":
        workspace = runtime["project_store"].replace_workspace_storylines(
            parsed["storylines"],
            source_xml_path=parsed["source_xml_path"],
            source_fileversion=parsed["source_fileversion"],
            article_id_assignments=parsed.get("article_id_assignments", {}),
        )
    else:
        before_count = len(runtime["project_store"].load_workspace().get("storylines", []))
        workspace = runtime["project_store"].merge_workspace_storylines(
            parsed["storylines"],
            source_xml_path=parsed["source_xml_path"],
            source_fileversion=parsed["source_fileversion"],
            article_id_assignments=parsed.get("article_id_assignments", {}),
        )
        after_count = len(workspace.get("storylines", []))
        return {
            "workspace": runtime["project_store"].get_workspace_summary(),
            "imported_storyline_count": len(parsed["storylines"]),
            "imported_article_id_count": len(parsed.get("article_id_assignments", {})),
            "mode": normalized_mode,
            "added_or_updated_count": len(parsed["storylines"]),
            "workspace_storyline_count_before": before_count,
            "workspace_storyline_count_after": after_count,
            "validation": runtime["validation"].validate_bundle(workspace.get("storylines", [])),
        }

    return {
        "workspace": runtime["project_store"].get_workspace_summary(),
        "imported_storyline_count": len(parsed["storylines"]),
        "imported_article_id_count": len(parsed.get("article_id_assignments", {})),
        "mode": normalized_mode,
        "validation": runtime["validation"].validate_bundle(workspace.get("storylines", [])),
    }


@mcp.tool()
def save_workspace_xml(xml_path: str = "", create_backup: bool = True) -> dict[str, Any]:
    runtime = _runtime()
    workspace = runtime["project_store"].load_workspace()
    projects = workspace.get("storylines", [])
    output_path = xml_path.strip() if xml_path.strip() else workspace.get("source_xml_path", "")
    if not output_path:
        output_path = str(runtime["xml_export"].export_storyline_bundle_xml(projects))
        return {
            "output_path": output_path,
            "used_workspace_source_path": False,
            "validation": runtime["validation"].validate_bundle(projects),
        }

    written_path = runtime["xml_export"].write_projects_xml_to_path(
        projects,
        output_path,
        source_fileversion=workspace.get("source_fileversion", "OOTP Storyline MCP Export"),
        create_backup=create_backup,
    )
    return {
        "output_path": str(written_path),
        "used_workspace_source_path": not bool(xml_path.strip()),
        "validation": runtime["validation"].validate_bundle(projects),
    }


@mcp.tool()
def get_project(project_id: str) -> dict[str, Any]:
    runtime = _runtime()
    return runtime["project_store"].load_project(project_id)


@mcp.tool()
def delete_project(project_id: str) -> dict[str, Any]:
    runtime = _runtime()
    return runtime["project_store"].delete_project(project_id)


@mcp.tool()
def create_storyline_project(
    project_id: str,
    random_frequency: int,
    subject: str,
    text: str,
    trigger_events: str = "",
    is_minor_league: bool = False,
    only_in_season: bool = False,
    only_in_offseason: bool = False,
    only_in_spring: bool = False,
) -> dict[str, Any]:
    runtime = _runtime()
    project = runtime["project_store"].create_project(
        project_id=project_id,
        random_frequency=random_frequency,
        subject=subject,
        text=text,
        trigger_events=trigger_events,
        is_minor_league=is_minor_league,
        only_in_season=only_in_season,
        only_in_offseason=only_in_offseason,
        only_in_spring=only_in_spring,
    )
    return _project_with_validation(project)


@mcp.tool()
def patch_storyline_project(project_id: str, patch_json: str) -> dict[str, Any]:
    runtime = _runtime()
    patch = json.loads(patch_json)
    project = runtime["project_store"].patch_project(project_id, patch)
    return _project_with_validation(project)


@mcp.tool()
def validate_storyline_project(project_id: str) -> dict[str, Any]:
    runtime = _runtime()
    project = runtime["project_store"].load_project(project_id)
    return runtime["validation"].validate_project(project)


@mcp.tool()
def validate_workspace() -> dict[str, Any]:
    runtime = _runtime()
    projects = runtime["project_store"].load_workspace().get("storylines", [])
    return runtime["validation"].validate_bundle(projects)


@mcp.tool()
def get_authoring_guidance() -> dict[str, Any]:
    return {
        "recommended_workflow": [
            "Keep one storyline per JSON file in the local projects directory.",
            "Use article_key and previous_article_keys while authoring instead of numeric ARTICLE ids.",
            "Import an existing XML file when you want to edit stock or previously exported storylines.",
            "Run project validation often, then run workspace validation before final XML export.",
            "Let export compile every project file into one storylines.xml and preserve stable numeric article ids through the local manifest.",
            "For Korean or other non-ASCII text, trust the written UTF-8 files over raw PowerShell rendering.",
        ],
        "why_project_files_are_better": (
            "OOTP reads one final storyline XML file, but authoring is safer when each storyline lives in its own JSON file. "
            "This server now treats the projects directory as the local source set and compiles it into one XML on save."
        ),
        "hot_reload_note": (
            "This server reloads local catalog, validation, export, import, and project-store modules on each tool call. "
            "Editing those modules should now reflect without a full server restart."
        ),
    }



def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
