from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .paths import EXPORTS_DIR


def _bool_to_ootp(value: Any) -> str:
    if value is True:
        return "1"
    if value is False:
        return "0"
    return str(value)


def _project_to_element(project: dict[str, Any]) -> ET.Element:
    root = ET.Element("STORYLINE_DATABASE", {"fileversion": "OOTP Storyline MCP Export"})
    storylines_node = ET.SubElement(root, "STORYLINES")
    _append_storyline_element(storylines_node, project)
    return root


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


def export_project_xml(project: dict[str, Any], output_filename: str = "") -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = output_filename or f"{project['id']}.xml"
    if not filename.lower().endswith(".xml"):
        filename = f"{filename}.xml"
    path = EXPORTS_DIR / filename

    root = _project_to_element(project)
    raw = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(raw).toprettyxml(indent="\t", encoding="UTF-8")
    path.write_bytes(pretty)
    return path


def export_storyline_bundle_xml(projects: list[dict[str, Any]], output_filename: str = "") -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = output_filename or "storyline_bundle.xml"
    if not filename.lower().endswith(".xml"):
        filename = f"{filename}.xml"
    path = EXPORTS_DIR / filename

    root = ET.Element("STORYLINE_DATABASE", {"fileversion": "OOTP Storyline MCP Export"})
    storylines_node = ET.SubElement(root, "STORYLINES")
    for project in projects:
        _append_storyline_element(storylines_node, project)

    raw = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(raw).toprettyxml(indent="\t", encoding="UTF-8")
    path.write_bytes(pretty)
    return path
