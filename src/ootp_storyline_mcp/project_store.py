from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import (
    ARTICLE_ID_MANIFEST_FILENAME,
    ARTICLE_ID_MANIFEST_PATH,
    LEGACY_WORKSPACE_PATH,
    PROJECTS_DIR,
    WORKSPACE_META_FILENAME,
    WORKSPACE_META_PATH,
)


WORKSPACE_ID = "storyline_workspace"
DEFAULT_NEXT_ARTICLE_ID = 900001
_META_FILENAMES = {
    WORKSPACE_META_FILENAME,
    ARTICLE_ID_MANIFEST_FILENAME,
    LEGACY_WORKSPACE_PATH.name,
}


def _empty_workspace_meta() -> dict[str, Any]:
    return {
        "id": WORKSPACE_ID,
        "source_xml_path": "",
        "source_fileversion": "",
    }


def _empty_manifest() -> dict[str, Any]:
    return {
        "next_article_id": DEFAULT_NEXT_ARTICLE_ID,
        "assignments": {},
    }


def _normalize_trigger_events(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(part).strip() for part in value if str(part).strip())
    if value is None:
        return ""
    return str(value)


def _safe_filename(project_id: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", project_id).strip("._") or "storyline"
    digest = hashlib.sha1(project_id.encode("utf-8")).hexdigest()[:8]
    return f"{stem}__{digest}.json"


def _project_file_path(project_id: str) -> Path:
    return PROJECTS_DIR / _safe_filename(project_id)


def _project_paths() -> list[Path]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        path
        for path in PROJECTS_DIR.glob("*.json")
        if path.name not in _META_FILENAMES
        and not path.name.startswith("storyline_workspace")
        and ".backup_" not in path.name
        and ".legacy." not in path.name
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_workspace_meta() -> dict[str, Any]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    if not WORKSPACE_META_PATH.exists():
        return _empty_workspace_meta()
    data = _read_json(WORKSPACE_META_PATH)
    meta = _empty_workspace_meta()
    meta.update(data)
    return meta


def save_workspace_meta(meta: dict[str, Any]) -> Path:
    normalized = _empty_workspace_meta()
    normalized.update(meta)
    return _write_json(WORKSPACE_META_PATH, normalized)


def load_article_id_manifest() -> dict[str, Any]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    if not ARTICLE_ID_MANIFEST_PATH.exists():
        return _empty_manifest()
    data = _read_json(ARTICLE_ID_MANIFEST_PATH)
    manifest = _empty_manifest()
    manifest["next_article_id"] = int(data.get("next_article_id", DEFAULT_NEXT_ARTICLE_ID))
    manifest["assignments"] = {
        str(key): int(value)
        for key, value in dict(data.get("assignments", {})).items()
        if str(value).strip()
    }
    if manifest["assignments"]:
        manifest["next_article_id"] = max(
            manifest["next_article_id"],
            max(manifest["assignments"].values()) + 1,
        )
    return manifest


def save_article_id_manifest(manifest: dict[str, Any]) -> Path:
    normalized = _empty_manifest()
    normalized["assignments"] = {
        str(key): int(value)
        for key, value in dict(manifest.get("assignments", {})).items()
    }
    next_article_id = int(manifest.get("next_article_id", DEFAULT_NEXT_ARTICLE_ID))
    if normalized["assignments"]:
        next_article_id = max(next_article_id, max(normalized["assignments"].values()) + 1)
    normalized["next_article_id"] = next_article_id
    return _write_json(ARTICLE_ID_MANIFEST_PATH, normalized)


def _default_article_key(index: int, article_id: int | None = None) -> str:
    if index == 0:
        return "main"
    if article_id is not None:
        return f"article_{article_id}"
    return f"article_{index + 1}"


def _dedupe_key(candidate: str, used: set[str]) -> str:
    base = candidate.strip() or "article"
    if base not in used:
        used.add(base)
        return base
    suffix = 2
    while True:
        deduped = f"{base}_{suffix}"
        if deduped not in used:
            used.add(deduped)
            return deduped
        suffix += 1


def _split_previous_ids(raw_previous_ids: Any) -> list[str]:
    if isinstance(raw_previous_ids, list):
        return [str(value).strip() for value in raw_previous_ids if str(value).strip()]
    if raw_previous_ids is None:
        return []
    return [part.strip() for part in str(raw_previous_ids).split(",") if part.strip()]


def _normalize_project(project: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int], bool]:
    normalized = deepcopy(project)
    changed = False

    normalized["id"] = str(normalized["id"])
    if "trigger_events" in normalized:
        trigger_events = _normalize_trigger_events(normalized.get("trigger_events", ""))
        changed = changed or trigger_events != normalized.get("trigger_events", "")
        normalized["trigger_events"] = trigger_events

    normalized["required_data"] = list(normalized.get("required_data", []))
    raw_articles = list(normalized.get("articles", []))

    manifest_entries: dict[str, int] = {}
    raw_id_to_key: dict[int, str] = {}
    normalized_articles: list[dict[str, Any]] = []
    used_keys: set[str] = set()
    article_keys: list[str] = []

    for index, article in enumerate(raw_articles):
        raw_id = article.get("id") if isinstance(article.get("id"), int) else None
        candidate_key = str(article.get("article_key") or _default_article_key(index, raw_id))
        article_key = _dedupe_key(candidate_key, used_keys)
        if article_key != article.get("article_key"):
            changed = True
        article_keys.append(article_key)
        if raw_id is not None:
            raw_id_to_key[raw_id] = article_key
            manifest_entries[f"{normalized['id']}:{article_key}"] = raw_id

    for index, article in enumerate(raw_articles):
        article_key = article_keys[index]
        normalized_article: dict[str, Any] = {}
        for key, value in article.items():
            if key in {"id", "previous_ids"}:
                changed = True
                continue
            normalized_article[key] = value
        normalized_article["article_key"] = article_key

        previous_article_keys = article.get("previous_article_keys")
        if isinstance(previous_article_keys, list):
            normalized_previous_keys = [
                str(value).strip() for value in previous_article_keys if str(value).strip()
            ]
        else:
            normalized_previous_keys = []
            for raw_previous in _split_previous_ids(article.get("previous_ids")):
                if raw_previous.isdigit():
                    previous_key = raw_id_to_key.get(int(raw_previous), f"article_{raw_previous}")
                else:
                    previous_key = raw_previous
                normalized_previous_keys.append(previous_key)
            if article.get("previous_ids"):
                changed = True

        if normalized_previous_keys:
            normalized_article["previous_article_keys"] = normalized_previous_keys
        elif "previous_article_keys" in normalized_article and not normalized_article["previous_article_keys"]:
            normalized_article.pop("previous_article_keys", None)
            changed = True

        normalized_articles.append(normalized_article)

    normalized["articles"] = normalized_articles
    return normalized, manifest_entries, changed


def _apply_manifest_entries_for_project(
    project_id: str,
    article_keys: list[str],
    manifest_entries: dict[str, int],
) -> None:
    manifest = load_article_id_manifest()
    prefix = f"{project_id}:"
    active_keys = {f"{project_id}:{article_key}" for article_key in article_keys}
    assignments = {
        key: value
        for key, value in manifest["assignments"].items()
        if not key.startswith(prefix) or key in active_keys
    }
    assignments.update({key: int(value) for key, value in manifest_entries.items()})
    manifest["assignments"] = assignments
    save_article_id_manifest(manifest)


def _save_project_to_path(path: Path, project: dict[str, Any], manifest_entries: dict[str, int] | None = None) -> Path:
    normalized, auto_manifest_entries, _ = _normalize_project(project)
    merged_manifest_entries = dict(auto_manifest_entries)
    if manifest_entries:
        merged_manifest_entries.update(
            {
                str(key): int(value)
                for key, value in manifest_entries.items()
                if str(key).startswith(f"{normalized['id']}:")
            }
        )
    _write_json(path, normalized)
    _apply_manifest_entries_for_project(
        str(normalized["id"]),
        [article["article_key"] for article in normalized.get("articles", [])],
        merged_manifest_entries,
    )
    return path


def _load_all_projects_with_paths() -> list[tuple[Path, dict[str, Any]]]:
    _migrate_legacy_workspace_if_needed()
    pairs: list[tuple[Path, dict[str, Any]]] = []
    aggregated_manifest_entries: dict[str, int] = {}

    for path in _project_paths():
        data = _read_json(path)
        normalized, manifest_entries, changed = _normalize_project(data)
        if changed:
            _write_json(path, normalized)
        pairs.append((path, normalized))
        aggregated_manifest_entries.update(manifest_entries)

    if aggregated_manifest_entries:
        manifest = load_article_id_manifest()
        assignments = dict(manifest.get("assignments", {}))
        assignments.update(aggregated_manifest_entries)
        manifest["assignments"] = assignments
        save_article_id_manifest(manifest)

    return pairs


def _migrate_legacy_workspace_if_needed() -> None:
    if not LEGACY_WORKSPACE_PATH.exists():
        return
    if _project_paths():
        return

    legacy_workspace = _read_json(LEGACY_WORKSPACE_PATH)
    meta = _empty_workspace_meta()
    meta["source_xml_path"] = str(legacy_workspace.get("source_xml_path", ""))
    meta["source_fileversion"] = str(legacy_workspace.get("source_fileversion", ""))
    save_workspace_meta(meta)

    manifest_entries: dict[str, int] = {}
    for storyline in list(legacy_workspace.get("storylines", [])):
        normalized, story_manifest_entries, _ = _normalize_project(storyline)
        _write_json(_project_file_path(str(normalized["id"])), normalized)
        manifest_entries.update(story_manifest_entries)

    manifest = _empty_manifest()
    manifest["assignments"] = manifest_entries
    if manifest_entries:
        manifest["next_article_id"] = max(
            DEFAULT_NEXT_ARTICLE_ID,
            max(manifest_entries.values()) + 1,
        )
    save_article_id_manifest(manifest)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = LEGACY_WORKSPACE_PATH.with_name(
        f"storyline_workspace.legacy.backup_{timestamp}.json"
    )
    LEGACY_WORKSPACE_PATH.replace(backup_path)


def load_workspace() -> dict[str, Any]:
    meta = load_workspace_meta()
    return {
        **meta,
        "storylines": load_projects(),
    }


def get_workspace_summary() -> dict[str, Any]:
    meta = load_workspace_meta()
    manifest = load_article_id_manifest()
    projects = list_projects()
    return {
        "id": meta["id"],
        "workspace_meta_path": str(WORKSPACE_META_PATH),
        "article_manifest_path": str(ARTICLE_ID_MANIFEST_PATH),
        "source_xml_path": meta.get("source_xml_path", ""),
        "source_fileversion": meta.get("source_fileversion", ""),
        "storyline_count": len(projects),
        "assigned_article_id_count": len(manifest.get("assignments", {})),
        "next_article_id": manifest.get("next_article_id", DEFAULT_NEXT_ARTICLE_ID),
    }


def list_projects() -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for path, data in _load_all_projects_with_paths():
        projects.append(
            {
                "id": data.get("id"),
                "path": str(path),
                "article_count": len(data.get("articles", [])),
                "required_data_count": len(data.get("required_data", [])),
            }
        )
    return projects


def load_projects(project_ids: list[str] | None = None) -> list[dict[str, Any]]:
    requested_ids = {str(project_id) for project_id in project_ids} if project_ids else None
    projects: list[dict[str, Any]] = []
    for _, data in _load_all_projects_with_paths():
        if requested_ids is not None and str(data.get("id")) not in requested_ids:
            continue
        projects.append(deepcopy(data))
    return projects


def load_project(project_id: str) -> dict[str, Any]:
    for _, data in _load_all_projects_with_paths():
        if str(data.get("id")) == project_id:
            return deepcopy(data)
    raise FileNotFoundError(f"Storyline not found: {project_id}")


def save_project(project: dict[str, Any], manifest_entries: dict[str, int] | None = None) -> Path:
    project_id = str(project["id"])
    existing_path = _project_file_path(project_id)
    for path, data in _load_all_projects_with_paths():
        if str(data.get("id")) == project_id:
            existing_path = path
            break
    return _save_project_to_path(existing_path, project, manifest_entries=manifest_entries)


def delete_project(project_id: str) -> dict[str, Any]:
    deleted_path: Path | None = None
    for path, data in _load_all_projects_with_paths():
        if str(data.get("id")) == project_id:
            deleted_path = path
            break
    if deleted_path is None:
        raise FileNotFoundError(f"Storyline not found: {project_id}")

    deleted_path.unlink(missing_ok=False)
    manifest = load_article_id_manifest()
    prefix = f"{project_id}:"
    manifest["assignments"] = {
        key: value
        for key, value in manifest["assignments"].items()
        if not key.startswith(prefix)
    }
    save_article_id_manifest(manifest)
    return {"id": project_id, "deleted": True}


def create_project(
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
    for _, existing in _load_all_projects_with_paths():
        if str(existing.get("id")) == project_id:
            raise FileExistsError(f"Storyline already exists: {project_id}")

    project: dict[str, Any] = {
        "id": project_id,
        "random_frequency": random_frequency,
        "required_data": [],
        "articles": [
            {
                "article_key": "main",
                "subject": subject,
                "text": text,
            }
        ],
    }
    normalized_trigger_events = _normalize_trigger_events(trigger_events)
    if normalized_trigger_events:
        project["trigger_events"] = normalized_trigger_events
    if is_minor_league:
        project["is_minor_league"] = True
    if only_in_season:
        project["only_in_season"] = True
    if only_in_offseason:
        project["only_in_offseason"] = True
    if only_in_spring:
        project["only_in_spring"] = True

    save_project(project)
    return project


def _resolve_article_key(project_id: str, articles: list[dict[str, Any]], selector: Any) -> str:
    if isinstance(selector, str) and selector.strip():
        article_key = selector.strip()
        for article in articles:
            if str(article.get("article_key")) == article_key:
                return article_key
        raise ValueError(f"Article key '{article_key}' not found in storyline {project_id}")

    if isinstance(selector, int):
        manifest = load_article_id_manifest()
        prefix = f"{project_id}:"
        for global_key, numeric_id in manifest.get("assignments", {}).items():
            if global_key.startswith(prefix) and int(numeric_id) == selector:
                return global_key.split(":", 1)[1]
        raise ValueError(f"Article id {selector} not found in storyline {project_id}")

    raise ValueError(f"Invalid article selector for storyline {project_id}: {selector}")


def patch_project(project_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_id)

    for key, value in patch.get("meta", {}).items():
        if key in {"id", "required_data", "articles"}:
            continue
        project[key] = value

    for key in patch.get("remove_meta_keys", []):
        if key in {"id", "required_data", "articles"}:
            continue
        project.pop(key, None)

    required_data = project.setdefault("required_data", [])
    for data_object in patch.get("add_required_data_objects", []):
        required_data.append(deepcopy(data_object))

    remove_required_indices = sorted(
        {int(index) for index in patch.get("remove_required_data_indices", [])},
        reverse=True,
    )
    for index in remove_required_indices:
        if index < 0 or index >= len(required_data):
            raise IndexError(f"required_data index out of range: {index}")
        required_data.pop(index)

    articles = project.setdefault("articles", [])
    for article in patch.get("add_articles", []):
        articles.append(deepcopy(article))

    for update_spec in patch.get("update_articles", []):
        selector = update_spec.get("article_key", update_spec.get("id"))
        article_key = _resolve_article_key(project_id, articles, selector)
        updates = dict(update_spec.get("updates", {}))
        updates.pop("id", None)
        for article in articles:
            if str(article.get("article_key")) == article_key:
                article.update(updates)
                break

    remove_article_keys = {
        str(article_key)
        for article_key in patch.get("remove_article_keys", [])
        if str(article_key).strip()
    }
    remove_article_ids = {
        int(article_id)
        for article_id in patch.get("remove_article_ids", [])
    }
    for article_id in remove_article_ids:
        remove_article_keys.add(_resolve_article_key(project_id, articles, article_id))

    if remove_article_keys:
        new_articles = [
            article
            for article in articles
            if str(article.get("article_key")) not in remove_article_keys
        ]
        if len(new_articles) == len(articles):
            missing = ", ".join(sorted(remove_article_keys))
            raise ValueError(f"Article keys not found in storyline {project_id}: {missing}")
        project["articles"] = new_articles

    save_project(project)
    return project


def replace_workspace_storylines(
    storylines: list[dict[str, Any]],
    source_xml_path: str = "",
    source_fileversion: str = "",
    article_id_assignments: dict[str, int] | None = None,
) -> dict[str, Any]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    for path in _project_paths():
        path.unlink(missing_ok=True)

    meta = _empty_workspace_meta()
    meta["source_xml_path"] = source_xml_path
    meta["source_fileversion"] = source_fileversion
    save_workspace_meta(meta)

    save_article_id_manifest(_empty_manifest())
    assignments = article_id_assignments or {}
    for storyline in storylines:
        project_id = str(storyline["id"])
        project_assignments = {
            key: int(value)
            for key, value in assignments.items()
            if key.startswith(f"{project_id}:")
        }
        save_project(storyline, manifest_entries=project_assignments)

    return load_workspace()


def merge_workspace_storylines(
    storylines: list[dict[str, Any]],
    source_xml_path: str = "",
    source_fileversion: str = "",
    article_id_assignments: dict[str, int] | None = None,
) -> dict[str, Any]:
    meta = load_workspace_meta()
    if source_xml_path:
        meta["source_xml_path"] = source_xml_path
    if source_fileversion:
        meta["source_fileversion"] = source_fileversion
    save_workspace_meta(meta)

    assignments = article_id_assignments or {}
    for storyline in storylines:
        project_id = str(storyline["id"])
        project_assignments = {
            key: int(value)
            for key, value in assignments.items()
            if key.startswith(f"{project_id}:")
        }
        save_project(storyline, manifest_entries=project_assignments)

    return load_workspace()
