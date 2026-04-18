import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .paths import PROJECTS_DIR, WORKSPACE_FILENAME, WORKSPACE_PATH


WORKSPACE_ID = "storyline_workspace"


def _legacy_project_paths() -> list[Path]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        path
        for path in PROJECTS_DIR.glob("*.json")
        if path.name != WORKSPACE_FILENAME
    )


def _normalize_trigger_events(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(part).strip() for part in value if str(part).strip())
    if value is None:
        return ""
    return str(value)


def _empty_workspace() -> dict[str, Any]:
    return {
        "id": WORKSPACE_ID,
        "source_xml_path": "",
        "source_fileversion": "",
        "storylines": [],
    }


def _normalize_workspace(data: dict[str, Any]) -> dict[str, Any]:
    if "storylines" in data:
        return {
            "id": data.get("id", WORKSPACE_ID),
            "source_xml_path": data.get("source_xml_path", ""),
            "source_fileversion": data.get("source_fileversion", ""),
            "storylines": list(data.get("storylines", [])),
        }
    # Legacy single-project shape. Wrap it into a workspace.
    return {
        "id": WORKSPACE_ID,
        "source_xml_path": "",
        "source_fileversion": "",
        "storylines": [data],
    }


def _load_legacy_projects() -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for path in _legacy_project_paths():
        try:
            projects.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return projects


def load_workspace(persist_if_migrated: bool = True) -> dict[str, Any]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    if WORKSPACE_PATH.exists():
        data = json.loads(WORKSPACE_PATH.read_text(encoding="utf-8"))
        return _normalize_workspace(data)

    workspace = _empty_workspace()
    legacy_projects = _load_legacy_projects()
    if legacy_projects:
        workspace["storylines"] = legacy_projects
        if persist_if_migrated:
            save_workspace(workspace)
    return workspace


def save_workspace(workspace: dict[str, Any]) -> Path:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_workspace(workspace)
    WORKSPACE_PATH.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return WORKSPACE_PATH


def get_workspace_summary() -> dict[str, Any]:
    workspace = load_workspace()
    return {
        "id": workspace["id"],
        "path": str(WORKSPACE_PATH),
        "source_xml_path": workspace.get("source_xml_path", ""),
        "source_fileversion": workspace.get("source_fileversion", ""),
        "storyline_count": len(workspace.get("storylines", [])),
    }


def replace_workspace_storylines(
    storylines: list[dict[str, Any]],
    source_xml_path: str = "",
    source_fileversion: str = "",
) -> dict[str, Any]:
    workspace = _empty_workspace()
    workspace["source_xml_path"] = source_xml_path
    workspace["source_fileversion"] = source_fileversion
    workspace["storylines"] = deepcopy(storylines)
    save_workspace(workspace)
    return workspace


def merge_workspace_storylines(
    storylines: list[dict[str, Any]],
    source_xml_path: str = "",
    source_fileversion: str = "",
) -> dict[str, Any]:
    workspace = load_workspace()
    existing_by_id = {
        str(storyline.get("id")): storyline
        for storyline in workspace.get("storylines", [])
    }
    for storyline in storylines:
        existing_by_id[str(storyline.get("id"))] = deepcopy(storyline)
    workspace["storylines"] = list(existing_by_id.values())
    if source_xml_path:
        workspace["source_xml_path"] = source_xml_path
    if source_fileversion:
        workspace["source_fileversion"] = source_fileversion
    save_workspace(workspace)
    return workspace


def _storylines(workspace: dict[str, Any]) -> list[dict[str, Any]]:
    return workspace.setdefault("storylines", [])


def _find_storyline(workspace: dict[str, Any], project_id: str) -> dict[str, Any]:
    for storyline in _storylines(workspace):
        if str(storyline.get("id")) == project_id:
            return storyline
    raise FileNotFoundError(f"Storyline not found in workspace: {project_id}")


def list_projects() -> list[dict[str, Any]]:
    workspace = load_workspace()
    projects: list[dict[str, Any]] = []
    for data in _storylines(workspace):
        projects.append(
            {
                "id": data.get("id"),
                "workspace_path": str(WORKSPACE_PATH),
                "article_count": len(data.get("articles", [])),
                "required_data_count": len(data.get("required_data", [])),
            }
        )
    return projects


def load_project(project_id: str) -> dict[str, Any]:
    workspace = load_workspace()
    return deepcopy(_find_storyline(workspace, project_id))


def save_project(project: dict[str, Any]) -> Path:
    workspace = load_workspace()
    storylines = _storylines(workspace)
    project_id = str(project["id"])
    for idx, existing in enumerate(storylines):
        if str(existing.get("id")) == project_id:
            storylines[idx] = deepcopy(project)
            save_workspace(workspace)
            return WORKSPACE_PATH
    storylines.append(deepcopy(project))
    save_workspace(workspace)
    return WORKSPACE_PATH


def delete_project(project_id: str) -> dict[str, Any]:
    workspace = load_workspace()
    storylines = _storylines(workspace)
    new_storylines = [storyline for storyline in storylines if str(storyline.get("id")) != project_id]
    if len(new_storylines) == len(storylines):
        raise FileNotFoundError(f"Storyline not found in workspace: {project_id}")
    workspace["storylines"] = new_storylines
    save_workspace(workspace)
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
    workspace = load_workspace()
    for existing in _storylines(workspace):
        if str(existing.get("id")) == project_id:
            raise FileExistsError(f"Storyline already exists in workspace: {project_id}")

    project: dict[str, Any] = {
        "id": project_id,
        "random_frequency": random_frequency,
        "required_data": [],
        "articles": [
            {
                "id": 900001,
                "subject": subject,
                "text": text,
            }
        ],
    }
    trigger_events = _normalize_trigger_events(trigger_events)
    if trigger_events:
        project["trigger_events"] = trigger_events
    if is_minor_league:
        project["is_minor_league"] = True
    if only_in_season:
        project["only_in_season"] = True
    if only_in_offseason:
        project["only_in_offseason"] = True
    if only_in_spring:
        project["only_in_spring"] = True

    _storylines(workspace).append(project)
    save_workspace(workspace)
    return project


def update_project_meta(project_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_id)
    for key, value in updates.items():
        if key in {"required_data", "articles"}:
            continue
        project[key] = value
    save_project(project)
    return project


def remove_project_meta_keys(project_id: str, keys: list[str]) -> dict[str, Any]:
    project = load_project(project_id)
    for key in keys:
        if key in {"id", "required_data", "articles"}:
            continue
        project.pop(key, None)
    save_project(project)
    return project


def add_required_data_object(project_id: str, data_object: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_id)
    project.setdefault("required_data", []).append(deepcopy(data_object))
    save_project(project)
    return project


def remove_required_data_object(project_id: str, index: int) -> dict[str, Any]:
    project = load_project(project_id)
    required_data = project.setdefault("required_data", [])
    if index < 0 or index >= len(required_data):
        raise IndexError(f"required_data index out of range: {index}")
    required_data.pop(index)
    save_project(project)
    return project


def add_article(project_id: str, article: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_id)
    project.setdefault("articles", []).append(deepcopy(article))
    save_project(project)
    return project


def remove_article(project_id: str, article_id: int) -> dict[str, Any]:
    project = load_project(project_id)
    articles = project.setdefault("articles", [])
    new_articles = [article for article in articles if int(article.get("id", -1)) != article_id]
    if len(new_articles) == len(articles):
        raise ValueError(f"Article id {article_id} not found in storyline {project_id}")
    project["articles"] = new_articles
    save_project(project)
    return project


def update_article(project_id: str, article_id: int, updates: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_id)
    for article in project.get("articles", []):
        if int(article.get("id")) == article_id:
            article.update(updates)
            save_project(project)
            return project
    raise ValueError(f"Article id {article_id} not found in storyline {project_id}")


def patch_project(project_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_id)

    for key, value in patch.get("meta", {}).items():
        if key in {"required_data", "articles"}:
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

    update_articles = patch.get("update_articles", [])
    for update_spec in update_articles:
        article_id = int(update_spec["id"])
        updates = update_spec.get("updates", {})
        for article in articles:
            if int(article.get("id")) == article_id:
                article.update(updates)
                break
        else:
            raise ValueError(f"Article id {article_id} not found in storyline {project_id}")

    remove_article_ids = {int(article_id) for article_id in patch.get("remove_article_ids", [])}
    if remove_article_ids:
        new_articles = [article for article in articles if int(article.get("id", -1)) not in remove_article_ids]
        if len(new_articles) == len(articles):
            missing = ", ".join(str(article_id) for article_id in sorted(remove_article_ids))
            raise ValueError(f"Article ids not found in storyline {project_id}: {missing}")
        project["articles"] = new_articles

    save_project(project)
    return project


def create_projects(project_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    for spec in project_specs:
        created.append(
            create_project(
                project_id=spec["project_id"],
                random_frequency=int(spec["random_frequency"]),
                subject=spec["subject"],
                text=spec["text"],
                trigger_events=_normalize_trigger_events(spec.get("trigger_events", "")),
                is_minor_league=bool(spec.get("is_minor_league", False)),
                only_in_season=bool(spec.get("only_in_season", False)),
                only_in_offseason=bool(spec.get("only_in_offseason", False)),
                only_in_spring=bool(spec.get("only_in_spring", False)),
            )
        )
    return created


def load_projects(project_ids: list[str] | None = None) -> list[dict[str, Any]]:
    workspace = load_workspace()
    storylines = _storylines(workspace)
    if not project_ids:
        return deepcopy(storylines)
    project_id_set = {str(project_id) for project_id in project_ids}
    return [deepcopy(storyline) for storyline in storylines if str(storyline.get("id")) in project_id_set]
