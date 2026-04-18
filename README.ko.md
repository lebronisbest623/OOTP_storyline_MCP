# OOTP Storyline MCP

OOTP 스토리라인을 JSON 프로젝트로 작성하고, 검증하고, OOTP 호환 XML로 내보내기 위한 MCP 서버입니다.

영문 메인 README: [README.md](README.md)

## 이 저장소의 목적

이 저장소는 **MCP 서버와 authoring toolkit 자체**를 제공하는 데 초점을 둡니다.

즉, MCP를 지원하는 코딩 에이전트가 이 서버에 붙어서:

- 스토리라인 스키마를 안전하게 조회하고
- 프로젝트를 작성하고
- 검증하고
- 최종 XML을 내보내는 흐름

을 지원하기 위한 저장소입니다.

## 주요 기능

- MCP 툴로 storyline attribute / trigger / data object type 조회
- JSON 기반 storyline 프로젝트 작성
- 단일 프로젝트 검증
- 다중 프로젝트 번들 검증
- OOTP 스타일 XML export
- 두 종류의 trigger 지원
  - `stock_xml`: stock storyline XML에서 직접 확인된 trigger
  - `engine_debug_trace`: OOTP debug trace에서 추가로 발견된 trigger

## 폴더 구조

- `src/ootp_storyline_mcp/`: MCP 서버 본체
- `catalog/`: 생성된 카탈로그 JSON
- `schemas/`: authored storyline JSON 스키마
- `projects/`: 로컬 storyline 프로젝트 폴더
- `exports/`: 생성된 XML 출력 폴더
- `stock/`: 선택적으로 둘 수 있는 stock XML 사이드카 복사본

## 빠른 시작

```powershell
cd C:\Users\user\OOTP_storyline_MCP
python run_server.py
```

## Codex 연결

Codex는 `~/.codex/config.toml`에서 MCP 서버 설정을 읽습니다.

다음 항목을 추가하면 됩니다.

```toml
[mcp_servers.ootp_storyline]
command = "python"
args = ["C:\\Users\\user\\OOTP_storyline_MCP\\run_server.py"]
enabled = true
```

저장 후 Codex를 다시 열거나 세션을 새로고침하면 서버가 잡힙니다.

## Claude Code 연결

Claude Code는 `.mcp.json` 프로젝트 설정 또는 CLI 추가 방식을 지원합니다.

### 방법 1: CLI로 추가

저장소 루트에서:

```powershell
claude mcp add --scope project ootp-storyline -- python run_server.py
```

확인:

```powershell
claude mcp list
```

Claude Code 안에서는 다음으로 상태를 확인할 수 있습니다.

```text
/mcp
```

### 방법 2: `.mcp.json` 작성

저장소 루트에 `.mcp.json`을 만들고 다음처럼 적습니다.

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

팀 단위로 프로젝트 설정을 공유하고 싶다면 이 방식이 편합니다.

## Cursor 연결

Cursor는 프로젝트의 `.cursor/mcp.json` 또는 글로벌 `~/.cursor/mcp.json`을 사용할 수 있습니다.

저장소 루트에 `.cursor/mcp.json`을 만들고 다음처럼 적습니다.

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

저장 후 Cursor를 재시작하거나 워크스페이스를 다시 열면 됩니다.

## 현재 MCP 툴

- `get_catalog_summary`
- `list_trigger_events`
- `get_trigger_event_details`
- `list_data_object_types`
- `list_attributes`
- `search_attributes`
- `get_attribute_details`
- `list_projects`
- `get_project`
- `delete_project`
- `create_storyline_project`
- `bulk_create_storyline_projects`
- `update_storyline_meta`
- `remove_storyline_meta_keys`
- `add_required_data_object`
- `remove_required_data_object`
- `add_article`
- `update_article`
- `remove_article`
- `validate_storyline_project`
- `bulk_validate_storyline_projects`
- `validate_storyline_bundle`
- `export_storyline_project_xml`
- `bulk_export_storyline_projects_xml`
- `export_storyline_bundle_xml`
- `get_authoring_guidance`

## 권장 작업 흐름

1. 이벤트 하나당 프로젝트 하나를 만듭니다.
2. `add_required_data_object`로 필요한 배우/대상 필터를 넣습니다.
3. `add_article` / `update_article`로 기사 블록을 채웁니다.
4. 잘못 넣은 키는 `remove_storyline_meta_keys`, `remove_required_data_object`, `remove_article`로 지웁니다.
5. `validate_storyline_project` 또는 `bulk_validate_storyline_projects`를 돌립니다.
6. 여러 프로젝트를 묶기 전에는 `validate_storyline_bundle`을 먼저 돌립니다.
7. 마지막에 `export_storyline_project_xml` 또는 `export_storyline_bundle_xml`로 XML을 생성합니다.

큰 작업은 프로젝트 하나에 계속 누적하기보다, 작은 프로젝트 여러 개를 만든 뒤 마지막에 번들 XML로 합치는 쪽이 훨씬 안전합니다.

## trigger source 참고

`list_trigger_events`에는 두 종류의 trigger가 섞여 나올 수 있습니다.

- `stock_xml`: stock OOTP storyline XML에 실제로 쓰인 trigger
- `engine_debug_trace`: OOTP debug trace를 통해 추가로 발견된 trigger

트리거 출처를 보고 싶으면 `get_trigger_event_details`를 쓰면 됩니다.

## stock XML 경로 해석 순서

카탈로그 로더는 stock XML을 아래 순서로 찾습니다.

1. `OOTP_STORYLINE_SOURCE_XML` 환경변수
2. 로컬 사이드카 파일 `stock/storylines_english.xml`
3. 기본 OOTP 설치 경로

이 방식으로 절대경로 의존을 줄이면서도, 일반 사용 흐름에서는 설치 경로를 강제로 박지 않게 했습니다.

## 공개 저장소 원칙

- `projects/*.json`은 기본적으로 git에 올리지 않습니다.
- `stock/storylines_english.xml`도 기본적으로 git에 올리지 않습니다.
- 이 저장소는 OOTP 원본 자산을 재배포하는 용도가 아니라, MCP 서버와 툴킷 자체를 배포하는 용도입니다.
