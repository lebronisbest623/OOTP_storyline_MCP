from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = PROJECT_ROOT / "catalog"
PROJECTS_DIR = PROJECT_ROOT / "projects"
EXPORTS_DIR = PROJECT_ROOT / "exports"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
STOCK_DIR = PROJECT_ROOT / "stock"
LOCAL_STORYLINES_XML = STOCK_DIR / "storylines_english.xml"
INSTALLED_STORYLINES_XML = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Out of the Park Baseball 27\data\storylines\default\storylines_english.xml"
)
