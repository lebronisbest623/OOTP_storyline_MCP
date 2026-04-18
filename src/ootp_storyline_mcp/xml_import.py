from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .catalog import load_catalog


def _attribute_types(section: str) -> dict[str, str]:
    catalog = load_catalog().data
    key = {
        "storyline": "storyline_attributes",
        "data_object": "data_object_attributes",
        "article": "article_attributes",
    }[section]
    return {
        record["name"]: record.get("inferred_type", "string")
        for record in catalog[key]
    }


def _coerce_value(inferred_type: str, raw_value: str) -> Any:
    value = raw_value.strip()
    if inferred_type == "integer":
        try:
            return int(value)
        except ValueError:
            return raw_value
    if inferred_type == "bool_flag":
        if value == "1":
            return True
        if value == "0":
            return False
        return raw_value
    return raw_value


def _coerce_attributes(attrs: dict[str, str], section: str) -> dict[str, Any]:
    type_map = _attribute_types(section)
    coerced: dict[str, Any] = {}
    for key, value in attrs.items():
        coerced[key] = _coerce_value(type_map.get(key, "string"), value)
    return coerced


def _child_text(node: ET.Element, tag: str) -> str | None:
    child = node.find(tag)
    if child is None:
        return None
    return child.text or ""


def _article_key_for_import(index: int, article_id: int | None = None) -> str:
    if index == 0:
        return "main"
    if article_id is not None:
        return f"article_{article_id}"
    return f"article_{index + 1}"


def _parse_storyline(storyline_node: ET.Element) -> tuple[dict[str, Any], dict[str, int]]:
    storyline = _coerce_attributes(dict(storyline_node.attrib), "storyline")
    storyline_id = str(storyline.get("id"))

    required_data: list[dict[str, Any]] = []
    for data_object_node in storyline_node.findall("./REQUIRED_DATA/DATA_OBJECT"):
        required_data.append(_coerce_attributes(dict(data_object_node.attrib), "data_object"))
    storyline["required_data"] = required_data

    raw_articles: list[tuple[dict[str, Any], list[str], int | None]] = []
    id_to_key: dict[int, str] = {}
    manifest_entries: dict[str, int] = {}

    for index, article_node in enumerate(storyline_node.findall("./ARTICLES/ARTICLE")):
        article = _coerce_attributes(dict(article_node.attrib), "article")
        subject = _child_text(article_node, "SUBJECT")
        text = _child_text(article_node, "TEXT")
        if subject is not None:
            article["subject"] = subject
        if text is not None:
            article["text"] = text
        reply = _child_text(article_node, "REPLY")
        if reply is not None:
            article["reply"] = reply
        injury_description = _child_text(article_node, "INJURY_DESCRIPTION")
        if injury_description is not None:
            article["injury_description"] = injury_description

        article_id = article.pop("id", None)
        article_id = article_id if isinstance(article_id, int) else None
        article_key = _article_key_for_import(index, article_id)
        article["article_key"] = article_key
        if article_id is not None:
            id_to_key[article_id] = article_key
            manifest_entries[f"{storyline_id}:{article_key}"] = article_id

        previous_ids = article.pop("previous_ids", "")
        raw_previous_ids = [part.strip() for part in str(previous_ids).split(",") if part.strip()]
        raw_articles.append((article, raw_previous_ids, article_id))

    articles: list[dict[str, Any]] = []
    for article, raw_previous_ids, _ in raw_articles:
        if raw_previous_ids:
            previous_article_keys: list[str] = []
            for raw_previous in raw_previous_ids:
                if raw_previous.isdigit():
                    previous_article_keys.append(
                        id_to_key.get(int(raw_previous), f"article_{raw_previous}")
                    )
                else:
                    previous_article_keys.append(raw_previous)
            article["previous_article_keys"] = previous_article_keys
        articles.append(article)

    storyline["articles"] = articles
    return storyline, manifest_entries


def parse_storyline_xml(xml_path: str) -> dict[str, Any]:
    path = Path(xml_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"XML file not found: {path}")

    tree = ET.parse(path)
    root = tree.getroot()
    storylines_node = root.find("STORYLINES")
    if storylines_node is None:
        raise ValueError(f"STORYLINES node not found in XML: {path}")

    storylines: list[dict[str, Any]] = []
    article_id_assignments: dict[str, int] = {}
    for node in storylines_node.findall("STORYLINE"):
        storyline, assignments = _parse_storyline(node)
        storylines.append(storyline)
        article_id_assignments.update(assignments)

    return {
        "source_xml_path": str(path),
        "source_fileversion": root.attrib.get("fileversion", ""),
        "storylines": storylines,
        "article_id_assignments": article_id_assignments,
    }


def backup_path_for(xml_path: str) -> Path:
    path = Path(xml_path).expanduser().resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.name}.backup_{timestamp}")
