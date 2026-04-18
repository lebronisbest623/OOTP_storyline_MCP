# OOTP Storyline MCP

OOTP 스토리라인 작성, 검증, XML export를 위한 MCP 서버입니다.

영문 메인 README: [README.md](README.md)

## 개요

- 스토리라인 프로젝트를 JSON으로 작성
- 단일 프로젝트 및 번들 검증
- OOTP 호환 XML export
- stock XML과 engine debug trace 양쪽에서 발견된 trigger 지원

## 요구 사항

- Python 3
- 아래 셋 중 하나로 stock XML 접근 가능해야 함
  1. `OOTP_STORYLINE_SOURCE_XML`
  2. `stock/storylines_english.xml`
  3. 기본 OOTP 설치 경로

## 실행

```powershell
cd C:\Users\user\OOTP_storyline_MCP
python run_server.py
```

## 클라이언트 연결

### Codex

`~/.codex/config.toml`에 추가:

```toml
[mcp_servers.ootp_storyline]
command = "python"
args = ["C:\\Users\\user\\OOTP_storyline_MCP\\run_server.py"]
enabled = true
```

### Claude Code

CLI로 추가:

```powershell
claude mcp add --scope project ootp-storyline -- python run_server.py
```

프로젝트 `.mcp.json`:

```json
{
  "mcpServers": {
    "ootp-storyline": {
      "command": "python",
      "args": ["run_server.py"],
      "env": {}
    }
  }
}
```

### Cursor

프로젝트 `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ootp-storyline": {
      "command": "python",
      "args": ["${workspaceFolder}/run_server.py"],
      "env": {}
    }
  }
}
```

## 핵심 MCP 툴

카탈로그:
- `get_catalog_summary`
- `list_trigger_events`
- `get_trigger_event_details`
- `list_data_object_types`
- `list_attributes`
- `search_attributes`
- `get_attribute_details`

프로젝트:
- `list_projects`
- `get_project`
- `delete_project`
- `create_storyline_project`
- `bulk_create_storyline_projects`
- `update_storyline_meta`
- `remove_storyline_meta_keys`

배우/기사:
- `add_required_data_object`
- `remove_required_data_object`
- `add_article`
- `update_article`
- `remove_article`

검증/출력:
- `validate_storyline_project`
- `bulk_validate_storyline_projects`
- `validate_storyline_bundle`
- `export_storyline_project_xml`
- `bulk_export_storyline_projects_xml`
- `export_storyline_bundle_xml`

가이드:
- `get_authoring_guidance`

## 참고

- `projects/*.json`은 기본적으로 git에 포함하지 않습니다.
- `stock/storylines_english.xml`도 기본적으로 git에 포함하지 않습니다.
- 이 저장소는 OOTP 원본 자산이 아니라 MCP 서버와 툴킷 자체를 배포합니다.
