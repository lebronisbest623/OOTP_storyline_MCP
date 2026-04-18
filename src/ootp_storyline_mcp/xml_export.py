from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import shutil
from typing import Any
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .paths import EXPORTS_DIR
from .project_store import load_article_id_manifest, save_article_id_manifest


DEFAULT_FILEVERSION = "OOTP Storyline MCP Export"


def _bool_to_ootp(value: Any) -> str:
    if value is True:
        return "1"
    if value is False:
        return "0"
    return str(value)


def _compile_projects(projects: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = load_article_id_manifest()
    assignments = dict(manifest.get("assignments", {}))
    next_article_id = int(manifest.get("next_article_id", 900001))

    compiled_projects: list[dict[str, Any]] = []
    active_assignment_keys: set[str] = set()

    for project in deepcopy(projects):
        project_id = str(project["id"])
        article_id_by_key: dict[str, int] = {}
        compiled_articles: list[dict[str, Any]] = []

        for article in project.get("articles", []):
            article_key = str(article["article_key"])
            manifest_key = f"{project_id}:{article_key}"
            active_assignment_keys.add(manifest_key)
            article_id = assignments.get(manifest_key)
            if not isinstance(article_id, int):
                article_id = next_article_id
                assignments[manifest_key] = article_id
                next_article_id += 1
            article_id_by_key[article_key] = article_id

        for article in project.get("articles", []):
            article_key = str(article["article_key"])
            compiled_article = {
                key: value
                for key, value in article.items()
                if key not in {"article_key", "previous_article_keys", "id", "previous_ids"}
            }
            compiled_article["id"] = article_id_by_key[article_key]

            previous_article_keys = [
                str(value).strip()
                for value in article.get("previous_article_keys", [])
                if str(value).strip()
            ]
            if previous_article_keys:
                missing_keys = [
                    previous_key
                    for previous_key in previous_article_keys
                    if previous_key not in article_id_by_key
                ]
                if missing_keys:
                    missing = ", ".join(missing_keys)
                    raise ValueError(
                        f"Storyline {project_id} references missing previous article keys: {missing}"
                    )
                compiled_article["previous_ids"] = ",".join(
                    str(article_id_by_key[previous_key]) for previous_key in previous_article_keys
                )

            compiled_articles.append(compiled_article)

        project["articles"] = compiled_articles
        compiled_projects.append(project)

    manifest["assignments"] = {
        key: value for key, value in assignments.items() if key in active_assignment_keys
    }
    if manifest["assignments"]:
        manifest["next_article_id"] = max(next_article_id, max(manifest["assignments"].values()) + 1)
    else:
        manifest["next_article_id"] = max(next_article_id, 900001)
    save_article_id_manifest(manifest)

    return compiled_projects, manifest


def _append_storyline_element(storylines_node: ET.Element, project: dict[str, Any]) -> ET.Element:
    storyline_attrs: dict[str, str] = {}
    for key, value in project.items():
        if key in {"required_data", "articles"}:
            continue
        storyline_attrs[key] = _bool_to_ootp(value)

    storyline_node = ET.SubElement(storylines_node, "STORYLINE", storyline_attrs)

    required_data = ET.SubElement(storyline_node, "REQUIRED_DATA")
    for data_object in project.get("required_data", []):
        attrs = {key: _bool_to_ootp(value) for key, value in data_object.items()}
        ET.SubElement(required_data, "DATA_OBJECT", attrs)

    articles_node = ET.SubElement(storyline_node, "ARTICLES")
    for article in project.get("articles", []):
        attrs = {
            key: _bool_to_ootp(value)
            for key, value in article.items()
            if key not in {"subject", "text", "injury_description", "reply"}
        }
        article_node = ET.SubElement(articles_node, "ARTICLE", attrs)
        subject_node = ET.SubElement(article_node, "SUBJECT")
        subject_node.text = article["subject"]
        text_node = ET.SubElement(article_node, "TEXT")
        text_node.text = article["text"]
        if article.get("reply"):
            reply_node = ET.SubElement(article_node, "REPLY")
            reply_node.text = article["reply"]
        if article.get("injury_description"):
            injury_node = ET.SubElement(article_node, "INJURY_DESCRIPTION")
            injury_node.text = article["injury_description"]

    return storyline_node


def _write_xml(root: ET.Element, path: Path) -> Path:
    raw = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(raw).toprettyxml(indent="\t", encoding="UTF-8")
    path.write_bytes(pretty)
    return path


def export_project_xml(project: dict[str, Any], output_filename: str = "") -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = output_filename or f"{project['id']}.xml"
    if not filename.lower().endswith(".xml"):
        filename = f"{filename}.xml"
    path = EXPORTS_DIR / filename

    compiled_projects, _ = _compile_projects([project])
    root = ET.Element("STORYLINE_DATABASE", {"fileversion": DEFAULT_FILEVERSION})
    storylines_node = ET.SubElement(root, "STORYLINES")
    _append_storyline_element(storylines_node, compiled_projects[0])
    return _write_xml(root, path)


def export_storyline_bundle_xml(projects: list[dict[str, Any]], output_filename: str = "") -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = output_filename or "storylines.xml"
    if not filename.lower().endswith(".xml"):
        filename = f"{filename}.xml"
    path = EXPORTS_DIR / filename

    compiled_projects, _ = _compile_projects(projects)
    root = ET.Element("STORYLINE_DATABASE", {"fileversion": DEFAULT_FILEVERSION})
    storylines_node = ET.SubElement(root, "STORYLINES")
    for project in compiled_projects:
        _append_storyline_element(storylines_node, project)
    return _write_xml(root, path)


def write_projects_xml_to_path(
    projects: list[dict[str, Any]],
    xml_path: str,
    source_fileversion: str = DEFAULT_FILEVERSION,
    create_backup: bool = False,
) -> Path:
    path = Path(xml_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if create_backup and path.exists():
        from .xml_import import backup_path_for

        backup_path = backup_path_for(str(path))
        shutil.copy2(path, backup_path)

    compiled_projects, _ = _compile_projects(projects)
    root = ET.Element(
        "STORYLINE_DATABASE",
        {"fileversion": source_fileversion or DEFAULT_FILEVERSION},
    )
    storylines_node = ET.SubElement(root, "STORYLINES")
    for project in compiled_projects:
        _append_storyline_element(storylines_node, project)
    return _write_xml(root, path)
