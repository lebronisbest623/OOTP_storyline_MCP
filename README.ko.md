# OOTP Storyline MCP

OOTP 스토리라인 작성, 검증, XML export를 위한 MCP 서버입니다.

영문 메인 README: [README.md](README.md)

## 개요

- 여러 STORYLINE 엔트리를 하나의 누적 workspace JSON 파일에 저장
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

전역 설정에서는 절대경로를 쓰는 것이 안전합니다. 상대경로는 MCP 설정 파일이 프로젝트 루트에 있을 때만 안정적으로 동작합니다.

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

Cursor도 프로젝트 로컬 설정이 아니라 전역 MCP 설정을 쓴다면 절대경로를 쓰는 쪽이 안전합니다.

## 핵심 MCP 툴

워크스페이스:
- `get_workspace`
- `import_storyline_xml`
- `save_workspace_xml`

카탈로그:
- `get_catalog_summary`
- `list_trigger_events`
- `list_data_object_types`
- `list_attributes`

스토리라인 엔트리:
- `get_project`
- `delete_project`
- `create_storyline_project`
- `patch_storyline_project`

검증/출력:
- `validate_storyline_project`
- `validate_workspace`

가이드:
- `get_authoring_guidance`
