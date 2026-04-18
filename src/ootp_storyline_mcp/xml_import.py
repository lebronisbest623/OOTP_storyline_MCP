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


def _parse_article(article_node: ET.Element) -> dict[str, Any]:
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
    return article


def _parse_storyline(storyline_node: ET.Element) -> dict[str, Any]:
    storyline = _coerce_attributes(dict(storyline_node.attrib), "storyline")
    required_data: list[dict[str, Any]] = []
    for data_object_node in storyline_node.findall("./REQUIRED_DATA/DATA_OBJECT"):
        required_data.append(_coerce_attributes(dict(data_object_node.attrib), "data_object"))
    storyline["required_data"] = required_data

    articles: list[dict[str, Any]] = []
    for article_node in storyline_node.findall("./ARTICLES/ARTICLE"):
        articles.append(_parse_article(article_node))
    storyline["articles"] = articles
    return storyline


def parse_storyline_xml(xml_path: str) -> dict[str, Any]:
    path = Path(xml_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"XML file not found: {path}")

    tree = ET.parse(path)
    root = tree.getroot()
    storylines_node = root.find("STORYLINES")
    if storylines_node is None:
        raise ValueError(f"STORYLINES node not found in XML: {path}")

    storylines = [_parse_storyline(node) for node in storylines_node.findall("STORYLINE")]
    return {
        "source_xml_path": str(path),
        "source_fileversion": root.attrib.get("fileversion", ""),
        "storylines": storylines,
    }


def merge_storylines(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    merged = {str(storyline.get("id")): storyline for storyline in existing}
    added = 0
    updated = 0
    for storyline in incoming:
        storyline_id = str(storyline.get("id"))
        if storyline_id in merged:
            updated += 1
        else:
            added += 1
        merged[storyline_id] = storyline
    ordered_ids = [str(storyline.get("id")) for storyline in existing]
    for storyline in incoming:
        storyline_id = str(storyline.get("id"))
        if storyline_id not in ordered_ids:
            ordered_ids.append(storyline_id)
    return [merged[storyline_id] for storyline_id in ordered_ids], added, updated


def backup_path_for(xml_path: str) -> Path:
    path = Path(xml_path).expanduser().resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.name}.backup_{timestamp}")
