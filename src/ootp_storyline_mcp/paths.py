from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = PROJECT_ROOT / "catalog"
PROJECTS_DIR = PROJECT_ROOT / "projects"
WORKSPACE_META_FILENAME = "_workspace.json"
WORKSPACE_META_PATH = PROJECTS_DIR / WORKSPACE_META_FILENAME
ARTICLE_ID_MANIFEST_FILENAME = "_article_ids.json"
ARTICLE_ID_MANIFEST_PATH = PROJECTS_DIR / ARTICLE_ID_MANIFEST_FILENAME
LEGACY_WORKSPACE_PATH = PROJECTS_DIR / "storyline_workspace.json"
EXPORTS_DIR = PROJECT_ROOT / "exports"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
STOCK_DIR = PROJECT_ROOT / "stock"
LOCAL_STORYLINES_XML = STOCK_DIR / "storylines_english.xml"
INSTALLED_STORYLINES_XML = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Out of the Park Baseball 27\data\storylines\default\storylines_english.xml"
)
