# OOTP Storyline MCP

OOTP 스토리라인을 JSON 프로젝트로 작성하고, 검증하고, OOTP XML로 내보내기 위한 MCP 서버입니다.

이 저장소는 **스토리라인 작성/검증/내보내기용 서버 본체**를 제공하는 데 초점을 둡니다.  
일반 사용자가 바로 MCP 서버를 붙여 쓰는 흐름을 기준으로 정리되어 있으며, 유지보수용 보조 스크립트는 공개 저장소에서 제외했습니다.

## 무엇을 할 수 있나

- OOTP 스토리라인 구조를 MCP 툴로 조회
- 프로젝트 단위 JSON 스토리라인 작성
- 프로젝트 단위 검증
- 여러 프로젝트를 묶은 번들 검증
- OOTP XML 형식으로 단건 또는 번들 export
- stock XML 기반 trigger와 engine debug trace 기반 trigger를 함께 카탈로그화

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

## 폴더 구조

- `src/ootp_storyline_mcp/`: MCP 서버 본체
- `catalog/`: trigger/attribute 카탈로그 JSON
- `schemas/`: authored storyline JSON 스키마
- `projects/`: 사용자가 작성하는 storyline 프로젝트 폴더
- `exports/`: 생성된 XML 출력 폴더
- `stock/`: 선택적으로 둘 수 있는 로컬 stock XML 사이드카 복사본

## 권장 작업 흐름

1. `create_storyline_project`로 프로젝트를 만듭니다.
2. `add_required_data_object`로 필요한 배우/대상 필터를 추가합니다.
3. `add_article` / `update_article`로 기사 내용을 채웁니다.
4. 잘못 넣은 키는 `remove_storyline_meta_keys`, `remove_required_data_object`, `remove_article`로 지웁니다.
5. `validate_storyline_project` 또는 `bulk_validate_storyline_projects`를 돌립니다.
6. 여러 프로젝트를 한 XML로 묶기 전에는 `validate_storyline_bundle`을 먼저 돌립니다.
7. 마지막에 `export_storyline_project_xml` 또는 `export_storyline_bundle_xml`로 XML을 생성합니다.

## 중요한 사용 팁

- 큰 작업은 **프로젝트 하나에 계속 누적하기보다**, 이벤트별로 작은 프로젝트를 여러 개 만든 뒤 마지막에 **번들 XML**로 묶는 쪽이 훨씬 안전합니다.
- `list_trigger_events`에는 두 종류의 trigger가 함께 보일 수 있습니다.
  - `stock_xml`: 기본 storyline XML에서 직접 확인된 trigger
  - `engine_debug_trace`: OOTP debug trace에서 추가로 확인된 trigger
- `league_nation_id` 같은 루트 속성은 스키마 단계에서 과도하게 막지 않고, 카탈로그 검증 단계에서 확인합니다.
- PowerShell은 한글 UTF-8 출력이 가끔 불안정할 수 있습니다. 최종 확인은 저장된 UTF-8 파일 기준으로 보는 것이 안전합니다.

## 빠른 시작

```powershell
cd C:\Users\user\OOTP_storyline_MCP
python run_server.py
```

## stock XML 경로 해석 순서

카탈로그 로더는 stock XML을 아래 순서로 찾습니다.

1. `OOTP_STORYLINE_SOURCE_XML` 환경변수
2. 로컬 사이드카 파일 `stock/storylines_english.xml`
3. 기본 OOTP 설치 경로

이 방식으로 절대경로 의존을 줄이면서도, 게임 원본 파일을 저장소에 기본 포함하지 않도록 했습니다.

## 공개 저장소 원칙

- 사용자 작성물인 `projects/*.json`은 기본적으로 git에 포함하지 않습니다.
- `stock/storylines_english.xml` 같은 OOTP 원본 자산도 기본적으로 저장소에 포함하지 않습니다.
- 이 저장소는 **MCP 서버와 authoring toolkit 자체**를 배포하는 것을 목표로 합니다.
