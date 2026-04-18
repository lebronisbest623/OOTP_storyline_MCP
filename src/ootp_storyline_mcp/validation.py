import json
from collections import defaultdict
from typing import Any

from jsonschema import Draft202012Validator

from .catalog import load_catalog
from .paths import SCHEMAS_DIR
from .project_store import load_article_id_manifest


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

    article_keys: list[str] = []
    for idx, article in enumerate(project.get("articles", [])):
        article_core = {
            "article_key",
            "subject",
            "text",
            "injury_description",
            "reply",
            "previous_article_keys",
        }
        article_allowed = allowed_article | article_core
        for key in article.keys():
            if key not in article_allowed:
                problems.append(f"articles[{idx}] attribute not seen in stock XML: {key}")
        article_keys.append(str(article.get("article_key", "")))

    if len(article_keys) != len(set(article_keys)):
        problems.append("article_key values must be unique within a project")

    article_key_set = {key for key in article_keys if key}
    for idx, article in enumerate(project.get("articles", [])):
        for previous_key in article.get("previous_article_keys", []):
            if str(previous_key) not in article_key_set:
                problems.append(
                    f"articles[{idx}] references missing previous_article_key: {previous_key}"
                )

    return {
        "valid": not problems,
        "error_count": len(problems),
        "errors": problems,
    }


def validate_bundle(projects: list[dict[str, Any]]) -> dict[str, Any]:
    problems: list[str] = []

    storyline_id_map: dict[str, list[str]] = defaultdict(list)
    project_validation_results: list[dict[str, Any]] = []
    active_manifest_keys: set[str] = set()

    for project in projects:
        project_id = str(project.get("id", "<missing-id>"))
        storyline_id_map[project_id].append(project_id)

        project_validation = validate_project(project)
        project_validation_results.append({"id": project_id, "validation": project_validation})

        for article in project.get("articles", []):
            article_key = str(article.get("article_key", "")).strip()
            if article_key:
                active_manifest_keys.add(f"{project_id}:{article_key}")

    for storyline_id, project_ids in sorted(storyline_id_map.items()):
        if len(project_ids) > 1:
            problems.append(
                f"bundle duplicate storyline id '{storyline_id}' appears {len(project_ids)} times"
            )

    manifest = load_article_id_manifest()
    article_id_map: dict[int, list[str]] = defaultdict(list)
    for manifest_key, article_id in manifest.get("assignments", {}).items():
        if manifest_key in active_manifest_keys:
            article_id_map[int(article_id)].append(manifest_key)

    for article_id, manifest_keys in sorted(article_id_map.items()):
        if len(manifest_keys) > 1:
            joined = ", ".join(sorted(manifest_keys))
            problems.append(
                f"bundle article id collision for compiled article {article_id}: {joined}"
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
