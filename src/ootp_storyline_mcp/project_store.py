import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .paths import PROJECTS_DIR


def _project_path(project_id: str) -> Path:
    return PROJECTS_DIR / f"{project_id}.json"


def _normalize_trigger_events(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(part).strip() for part in value if str(part).strip())
    if value is None:
        return ""
    return str(value)


def list_projects() -> list[dict[str, Any]]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    projects: list[dict[str, Any]] = []
    for path in sorted(PROJECTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            projects.append({"id": path.stem, "path": str(path), "status": "invalid_json"})
            continue
        projects.append(
            {
                "id": data.get("id", path.stem),
                "path": str(path),
                "article_count": len(data.get("articles", [])),
                "required_data_count": len(data.get("required_data", [])),
            }
        )
    return projects


def load_project(project_id: str) -> dict[str, Any]:
    path = _project_path(project_id)
    if not path.exists():
        raise FileNotFoundError(f"Project not found: {project_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_project(project: dict[str, Any]) -> Path:
    project_id = project["id"]
    path = _project_path(project_id)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(project, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def delete_project(project_id: str) -> dict[str, Any]:
    path = _project_path(project_id)
    if not path.exists():
        raise FileNotFoundError(f"Project not found: {project_id}")
    path.unlink()
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
    if _project_path(project_id).exists():
        raise FileExistsError(f"Project already exists: {project_id}")

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

    save_project(project)
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
        raise ValueError(f"Article id {article_id} not found in project {project_id}")
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
    raise ValueError(f"Article id {article_id} not found in project {project_id}")


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
    if not project_ids:
        project_ids = [record["id"] for record in list_projects()]
    return [load_project(project_id) for project_id in project_ids]
