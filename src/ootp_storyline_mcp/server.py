import importlib
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import catalog as catalog_module
from . import project_store as project_store_module
from . import validation as validation_module
from . import xml_export as xml_export_module

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
    return {
        "catalog": catalog_module,
        "project_store": project_store_module,
        "validation": validation_module,
        "xml_export": xml_export_module,
    }



def _lookup(records: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    name_lower = name.lower()
    for record in records:
        if record["name"] == name or record["name"].lower() == name_lower:
            return record
    return None



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



def _resolve_projects_from_json(project_ids_json: str = "") -> list[dict[str, Any]]:
    runtime = _runtime()
    if not project_ids_json.strip():
        return runtime["project_store"].load_projects()
    project_ids = json.loads(project_ids_json)
    return runtime["project_store"].load_projects(project_ids)


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
def list_trigger_events(source: str = "") -> list[dict[str, Any]]:
    records = _catalog()["trigger_events"]
    source_filter = source.strip().lower().replace("-", "_")
    if not source_filter:
        return records
    return [record for record in records if source_filter in record.get("sources", [])]


@mcp.tool()
def get_trigger_event_details(name: str) -> dict[str, Any] | None:
    return _lookup(_catalog()["trigger_events"], name)


@mcp.tool()
def list_data_object_types() -> list[dict[str, Any]]:
    return _catalog()["data_object_types"]


@mcp.tool()
def list_attributes(section: str) -> list[dict[str, Any]]:
    data = _catalog()
    mapping = {
        "storyline": data["storyline_attributes"],
        "data_object": data["data_object_attributes"],
        "article": data["article_attributes"],
    }
    return mapping[_normalize_section(section)]


@mcp.tool()
def search_attributes(query: str, section: str = "") -> list[dict[str, Any]]:
    query_lower = query.strip().lower()
    if not query_lower:
        return []

    sections = ["storyline", "data_object", "article"]
    if section.strip():
        sections = [_normalize_section(section)]

    results: list[dict[str, Any]] = []
    for current_section in sections:
        for record in list_attributes(current_section):
            haystacks = [record["name"].lower(), *(sample.lower() for sample in record.get("samples", []))]
            if any(query_lower in hay for hay in haystacks):
                results.append({"section": current_section, **record})
    return results


@mcp.tool()
def get_attribute_details(section: str, name: str) -> dict[str, Any] | None:
    normalized_section = _normalize_section(section)
    records = list_attributes(normalized_section)
    record = _lookup(records, name)
    if record is None:
        return None
    return {"section": normalized_section, **record}


@mcp.tool()
def list_projects() -> list[dict[str, Any]]:
    runtime = _runtime()
    return runtime["project_store"].list_projects()


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
def bulk_create_storyline_projects(projects_json: str) -> dict[str, Any]:
    runtime = _runtime()
    specs = json.loads(projects_json)
    projects = runtime["project_store"].create_projects(specs)
    return {
        "created_count": len(projects),
        "projects": [
            {
                "id": project["id"],
                "validation": runtime["validation"].validate_project(project),
            }
            for project in projects
        ],
    }


@mcp.tool()
def update_storyline_meta(project_id: str, updates_json: str) -> dict[str, Any]:
    runtime = _runtime()
    updates = json.loads(updates_json)
    project = runtime["project_store"].update_project_meta(project_id, updates)
    return _project_with_validation(project)


@mcp.tool()
def remove_storyline_meta_keys(project_id: str, keys_json: str) -> dict[str, Any]:
    runtime = _runtime()
    keys = json.loads(keys_json)
    project = runtime["project_store"].remove_project_meta_keys(project_id, keys)
    return _project_with_validation(project)


@mcp.tool()
def add_required_data_object(project_id: str, data_object_json: str) -> dict[str, Any]:
    runtime = _runtime()
    data_object = json.loads(data_object_json)
    project = runtime["project_store"].add_required_data_object(project_id, data_object)
    return _project_with_validation(project)


@mcp.tool()
def remove_required_data_object(project_id: str, index: int) -> dict[str, Any]:
    runtime = _runtime()
    project = runtime["project_store"].remove_required_data_object(project_id, index)
    return _project_with_validation(project)


@mcp.tool()
def add_article(project_id: str, article_json: str) -> dict[str, Any]:
    runtime = _runtime()
    article = json.loads(article_json)
    project = runtime["project_store"].add_article(project_id, article)
    return _project_with_validation(project)


@mcp.tool()
def update_article(project_id: str, article_id: int, updates_json: str) -> dict[str, Any]:
    runtime = _runtime()
    updates = json.loads(updates_json)
    project = runtime["project_store"].update_article(project_id, article_id, updates)
    return _project_with_validation(project)


@mcp.tool()
def remove_article(project_id: str, article_id: int) -> dict[str, Any]:
    runtime = _runtime()
    project = runtime["project_store"].remove_article(project_id, article_id)
    return _project_with_validation(project)


@mcp.tool()
def validate_storyline_project(project_id: str) -> dict[str, Any]:
    runtime = _runtime()
    project = runtime["project_store"].load_project(project_id)
    return runtime["validation"].validate_project(project)


@mcp.tool()
def bulk_validate_storyline_projects(project_ids_json: str = "") -> dict[str, Any]:
    runtime = _runtime()
    projects = _resolve_projects_from_json(project_ids_json)
    results = []
    valid_count = 0
    for project in projects:
        validation = runtime["validation"].validate_project(project)
        if validation["valid"]:
            valid_count += 1
        results.append({"id": project["id"], "validation": validation})
    return {
        "project_count": len(projects),
        "valid_count": valid_count,
        "results": results,
    }


@mcp.tool()
def validate_storyline_bundle(project_ids_json: str = "") -> dict[str, Any]:
    runtime = _runtime()
    projects = _resolve_projects_from_json(project_ids_json)
    return runtime["validation"].validate_bundle(projects)


@mcp.tool()
def export_storyline_project_xml(project_id: str, output_filename: str = "") -> dict[str, Any]:
    runtime = _runtime()
    project = runtime["project_store"].load_project(project_id)
    validation = runtime["validation"].validate_project(project)
    output_path = runtime["xml_export"].export_project_xml(project, output_filename)
    return {
        "output_path": str(output_path),
        "validation": validation,
    }


@mcp.tool()
def bulk_export_storyline_projects_xml(project_ids_json: str = "") -> dict[str, Any]:
    runtime = _runtime()
    projects = _resolve_projects_from_json(project_ids_json)
    outputs = []
    for project in projects:
        output_path = runtime["xml_export"].export_project_xml(project)
        outputs.append(
            {
                "id": project["id"],
                "output_path": str(output_path),
                "validation": runtime["validation"].validate_project(project),
            }
        )
    return {
        "project_count": len(projects),
        "outputs": outputs,
    }


@mcp.tool()
def export_storyline_bundle_xml(
    project_ids_json: str = "",
    output_filename: str = "",
    export_even_if_invalid: bool = False,
) -> dict[str, Any]:
    runtime = _runtime()
    projects = _resolve_projects_from_json(project_ids_json)
    bundle_validation = runtime["validation"].validate_bundle(projects)
    output_path = None
    if bundle_validation["valid"] or export_even_if_invalid:
        output_path = runtime["xml_export"].export_storyline_bundle_xml(projects, output_filename)
    return {
        "project_count": len(projects),
        "output_path": str(output_path) if output_path else None,
        "bundle_validation": bundle_validation,
        "exported": output_path is not None,
    }


@mcp.tool()
def get_authoring_guidance() -> dict[str, Any]:
    return {
        "recommended_workflow": [
            "Prefer one project per event or storyline concept.",
            "Use multiple small projects and combine them with a bundle XML for large sets.",
            "Run project validation often, then run bundle validation before final export.",
            "Treat engine_debug_trace trigger events as valid but distinct from stock_xml triggers.",
            "For Korean or other non-ASCII text, trust the written UTF-8 files over raw PowerShell rendering.",
        ],
        "why_multi_project_is_safer": (
            "Different triggers, seasonal gates, and REQUIRED_DATA shapes tend to conflict when many unrelated "
            "events accumulate in one project. Small projects stay easier to validate, edit, and remove."
        ),
        "hot_reload_note": (
            "This server reloads local catalog, validation, export, and project-store modules on each tool call. "
            "Editing those modules should now reflect without a full server restart."
        ),
    }



def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
