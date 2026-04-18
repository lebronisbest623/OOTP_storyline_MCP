# OOTP Storyline MCP

OOTP 스토리라인을 로컬 JSON 파일로 편집하고, 다시 하나의 OOTP 호환 XML로 합쳐주는 MCP 서버입니다.

영문 메인 README: [README.md](README.md)

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

## 저장 구조

- `projects/*.json`: STORYLINE 하나당 JSON 하나
- `projects/_workspace.json`: 원본 XML 경로 같은 로컬 메타데이터
- `projects/_article_ids.json`: export 시 유지되는 안정적인 `ARTICLE id` 매핑
- `save_workspace_xml`: 모든 프로젝트 JSON을 하나의 XML로 컴파일

## 권장 워크플로우

1. `import_storyline_xml`
2. `get_workspace`
3. `get_project`
4. `patch_storyline_project`
5. `validate_storyline_project` 또는 `validate_workspace`
6. `save_workspace_xml`

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

전역 `~/.mcp.json`:

```json
{
  "mcpServers": {
    "ootp-storyline": {
      "type": "stdio",
      "command": "python",
      "args": ["C:\\Users\\<user>\\OOTP_storyline_MCP\\run_server.py"],
      "env": {}
    }
  }
}
```

전역 설정에서는 절대경로를 쓰는 것이 안전합니다.

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

Cursor도 전역 MCP 설정을 쓴다면 절대경로를 쓰는 쪽이 안전합니다.

## 핵심 MCP 툴

카탈로그:
- `get_catalog_summary`
- `list_trigger_events`
- `list_data_object_types`
- `list_attributes`

워크스페이스:
- `get_workspace`
- `import_storyline_xml`
- `save_workspace_xml`

스토리라인:
- `get_project`
- `delete_project`
- `create_storyline_project`
- `patch_storyline_project`

검증:
- `validate_storyline_project`
- `validate_workspace`

가이드:
- `get_authoring_guidance`
