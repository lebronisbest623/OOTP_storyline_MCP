import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .catalog import load_catalog
from .paths import SCHEMAS_DIR


SCHEMA_PATH = SCHEMAS_DIR / "storyline.schema.json"


def _allowed_attribute_names(section: str) -> set[str]:
    catalog = load_catalog().data
    key = {
        "storyline": "storyline_attributes",
        "data_object": "data_object_attributes",
        "article": "article_attributes",
    }[section]
    return {record["name"] for record in catalog[key]}


def _allowed_trigger_events() -> set[str]:
    catalog = load_catalog().data
    return {record["name"] for record in catalog["trigger_events"]}


def validate_project(project: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(project), key=lambda e: list(e.absolute_path))

    problems: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.absolute_path) or "<root>"
        problems.append(f"{path}: {error.message}")

    allowed_storyline = _allowed_attribute_names("storyline")
    allowed_data_object = _allowed_attribute_names("data_object")
    allowed_article = _allowed_attribute_names("article")
    allowed_triggers = _allowed_trigger_events()

    storyline_core = {"id", "required_data", "articles"}
    storyline_allowed = allowed_storyline | storyline_core
    for key in project.keys():
        if key not in storyline_allowed:
            problems.append(f"storyline attribute not seen in stock XML: {key}")

    trigger_events = str(project.get("trigger_events", "")).strip()
    if trigger_events:
        for trigger in [part.strip() for part in trigger_events.split(",") if part.strip()]:
            if trigger not in allowed_triggers:
                problems.append(f"trigger event not seen in stock XML or engine debug inventory: {trigger}")

    for idx, data_object in enumerate(project.get("required_data", [])):
        for key in data_object.keys():
            if key not in allowed_data_object:
                problems.append(f"required_data[{idx}] attribute not seen in stock XML: {key}")

    for idx, article in enumerate(project.get("articles", [])):
        article_core = {"id", "subject", "text", "injury_description", "reply"}
        article_allowed = allowed_article | article_core
        for key in article.keys():
            if key not in article_allowed:
                problems.append(f"articles[{idx}] attribute not seen in stock XML: {key}")

    article_ids = [article.get("id") for article in project.get("articles", [])]
    if len(article_ids) != len(set(article_ids)):
        problems.append("article ids must be unique within a project")

    return {
        "valid": not problems,
        "error_count": len(problems),
        "errors": problems,
    }


def validate_bundle(projects: list[dict[str, Any]]) -> dict[str, Any]:
    problems: list[str] = []

    storyline_id_map: dict[str, list[str]] = defaultdict(list)
    article_id_map: dict[int, list[str]] = defaultdict(list)
    project_validation_results: list[dict[str, Any]] = []

    for project in projects:
        project_id = str(project.get("id", "<missing-id>"))
        storyline_id_map[project_id].append(project_id)

        project_validation = validate_project(project)
        project_validation_results.append({"id": project_id, "validation": project_validation})
        for article in project.get("articles", []):
            article_id = article.get("id")
            if isinstance(article_id, int):
                article_id_map[article_id].append(project_id)

    for storyline_id, project_ids in sorted(storyline_id_map.items()):
        if len(project_ids) > 1:
            problems.append(
                f"bundle duplicate storyline id '{storyline_id}' appears {len(project_ids)} times"
            )

    for article_id, project_ids in sorted(article_id_map.items()):
        unique_projects = sorted(set(project_ids))
        if len(unique_projects) > 1:
            joined = ", ".join(unique_projects)
            problems.append(
                f"bundle article id collision for article {article_id} across projects: {joined}"
            )

    invalid_project_count = sum(
        1 for result in project_validation_results if not result["validation"]["valid"]
    )

    return {
        "valid": invalid_project_count == 0 and not problems,
        "error_count": invalid_project_count + len(problems),
        "errors": problems,
        "project_count": len(projects),
        "invalid_project_count": invalid_project_count,
        "project_validations": project_validation_results,
    }
