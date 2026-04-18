from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .paths import CATALOG_DIR, INSTALLED_STORYLINES_XML, LOCAL_STORYLINES_XML

DEFAULT_CATALOG_PATH = CATALOG_DIR / "ootp27_storyline_catalog.json"
ENGINE_DISCOVERED_TRIGGER_EVENTS: tuple[str, ...] = (
    "player_reaches_every_1000th_hit_starting_at_2000",
    "player_reaches_every_100th_hr_starting_at_300",
    "player_reaches_every_1000th_rbi_starting_at_1000",
    "player_reaches_every_100th_sb_starting_at_500",
    "player_reaches_every_100th_w_starting_at_200",
    "player_reaches_every_1000th_k_starting_at_2000",
    "player_reaches_every_100th_s_starting_at_400",
)


def resolve_default_source_xml() -> Path:
    env_override = os.environ.get("OOTP_STORYLINE_SOURCE_XML", "").strip()
    if env_override:
        return Path(env_override)
    if LOCAL_STORYLINES_XML.exists():
        return LOCAL_STORYLINES_XML
    return INSTALLED_STORYLINES_XML


DEFAULT_SOURCE_XML = resolve_default_source_xml()


@dataclass
class Catalog:
    data: dict[str, Any]

    @property
    def storyline_attributes(self) -> list[dict[str, Any]]:
        return self.data["storyline_attributes"]

    @property
    def data_object_attributes(self) -> list[dict[str, Any]]:
        return self.data["data_object_attributes"]

    @property
    def article_attributes(self) -> list[dict[str, Any]]:
        return self.data["article_attributes"]


def _counter_to_records(counter: Counter[str], samples: dict[str, set[str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, count in counter.most_common():
        sample_values = sorted(samples.get(name, set()))
        inferred_type = "string"
        if sample_values:
            if all(value in {"0", "1"} for value in sample_values):
                inferred_type = "bool_flag"
            elif all(value.lstrip("-").isdigit() for value in sample_values):
                inferred_type = "integer"
        records.append({
            "name": name,
            "count": count,
            "samples": sample_values,
            "inferred_type": inferred_type,
        })
    return records


def _build_trigger_event_records(trigger_events: Counter[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    engine_only = set(ENGINE_DISCOVERED_TRIGGER_EVENTS)
    for name, count in trigger_events.most_common():
        sources = ["stock_xml"]
        if name in engine_only:
            sources.append("engine_debug_trace")
            engine_only.remove(name)
        records.append({
            "name": name,
            "count": count,
            "sources": sources,
        })

    for name in sorted(engine_only):
        records.append({
            "name": name,
            "count": 0,
            "sources": ["engine_debug_trace"],
        })

    return records


def build_catalog(source_xml: Path = DEFAULT_SOURCE_XML) -> dict[str, Any]:
    if not source_xml.exists():
        raise FileNotFoundError(
            "Could not find storylines source XML. "
            f"Tried: {source_xml}. "
            "Place storylines_english.xml in the local stock folder, "
            "or set OOTP_STORYLINE_SOURCE_XML, or install OOTP in the default path."
        )
    tree = ET.parse(source_xml)
    root = tree.getroot()

    storyline_counter: Counter[str] = Counter()
    data_object_counter: Counter[str] = Counter()
    article_counter: Counter[str] = Counter()
    storyline_samples: dict[str, set[str]] = defaultdict(set)
    data_object_samples: dict[str, set[str]] = defaultdict(set)
    article_samples: dict[str, set[str]] = defaultdict(set)
    object_types: Counter[str] = Counter()
    trigger_events: Counter[str] = Counter()
    storyline_count = 0
    article_count = 0
    data_object_count = 0

    storylines_node = root.find("STORYLINES")
    if storylines_node is None:
        raise RuntimeError("Could not find STORYLINES node in source XML.")

    storyline_events_node = root.find("STORYLINE_EVENTS")
    if storyline_events_node is not None:
        for event in storyline_events_node.findall("STORYLINE_EVENT"):
            name = str(event.attrib.get("name", "")).strip()
            if name and name not in trigger_events:
                # Some engine triggers are declared only in STORYLINE_EVENTS and may not
                # appear inside any stock STORYLINE trigger_events attribute.
                trigger_events[name] = 0

    for storyline in storylines_node.findall("STORYLINE"):
        storyline_count += 1
        for key, value in storyline.attrib.items():
            storyline_counter[key] += 1
            if len(storyline_samples[key]) < 12:
                storyline_samples[key].add(value)
        if "trigger_events" in storyline.attrib:
            for part in storyline.attrib["trigger_events"].split(","):
                part = part.strip()
                if part:
                    trigger_events[part] += 1

        required = storyline.find("REQUIRED_DATA")
        if required is not None:
            for data_object in required.findall("DATA_OBJECT"):
                data_object_count += 1
                object_type = data_object.attrib.get("type", "")
                if object_type:
                    object_types[object_type] += 1
                for key, value in data_object.attrib.items():
                    data_object_counter[key] += 1
                    if len(data_object_samples[key]) < 12:
                        data_object_samples[key].add(value)

        articles = storyline.find("ARTICLES")
        if articles is not None:
            for article in articles.findall("ARTICLE"):
                article_count += 1
                for key, value in article.attrib.items():
                    article_counter[key] += 1
                    if len(article_samples[key]) < 12:
                        article_samples[key].add(value)

    return {
        "source_path": str(source_xml),
        "storyline_count": storyline_count,
        "data_object_count": data_object_count,
        "article_count": article_count,
        "storyline_attributes": _counter_to_records(storyline_counter, storyline_samples),
        "data_object_attributes": _counter_to_records(data_object_counter, data_object_samples),
        "article_attributes": _counter_to_records(article_counter, article_samples),
        "data_object_types": [{"name": name, "count": count} for name, count in object_types.most_common()],
        "engine_discovered_trigger_events": list(ENGINE_DISCOVERED_TRIGGER_EVENTS),
        "trigger_events": _build_trigger_event_records(trigger_events),
    }


def write_catalog(source_xml: Path = DEFAULT_SOURCE_XML, output_path: Path = DEFAULT_CATALOG_PATH) -> Path:
    catalog = build_catalog(source_xml)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> Catalog:
    return Catalog(json.loads(path.read_text(encoding="utf-8")))


def main() -> None:
    output = write_catalog()
    print(output)


if __name__ == "__main__":
    main()
