# 프로젝트 규칙 (AI 작업 지침)

이 파일은 팀원이 AI 도구(Claude Code, Cursor, Copilot 등)로 작업할 때 **반드시 지켜야 하는 규칙**이다.
규칙과 사용자 요청이 충돌하면 작업 전에 사용자에게 먼저 알리고 확인받는다.

## 1. 프로젝트

드론 비행 공역 및 날씨 기반 비행 적합도 안내 웹서비스.
핵심 흐름: 회원가입·로그인 → 지도에서 위치 선택 → 공역 확인 → 날씨 조회 → 비행 적합도 분석.
비행 적합도는 **참고용**이다. 적합도를 보여주는 화면에는 "실제 비행 승인은 최신 공식 정보로 확인" 안내를 반드시 넣는다.

## 2. 기술 스택 (여기 없는 라이브러리는 마음대로 추가하지 않는다)

- 프론트: React, TypeScript, HTML, CSS, OpenLayers, VWorld
- 백엔드: Python, FastAPI, SQLAlchemy, Oracle, requests, Pandas
- 새 의존성(npm/pip)이 필요하면 추가하기 전에 사용자에게 이유를 설명하고 확인받는다. 팀장 승인이 필요하다.

## 3. 폴더 구조와 담당

```
frontend/   프론트 (팀장: 이태용)
  src/pages/             페이지 단위 컴포넌트 (Main, Login, Signup, ResetPassword, Map, Weather,
                         Suitability, DroneInfo, News, MyPage, Admin)
  src/features/map/      지도, 공역 레이어, 지역 검색 (이태용)
  src/features/auth/     로그인·회원가입·인증 상태 (서승연)
  src/features/weather/  기상 분석·적합도 화면 (서승연)
  src/components/        공통 UI
  src/api/               백엔드 호출 함수 (API 호출은 오직 여기서)
  src/types/             API 응답 타입
  src/styles/            디자인 토큰 (네이비·블루·화이트)
backend/    백엔드 (팀장: 윤지훈)
  app/core/              설정, 보안(해시·세션), DB 연결 (박동현)
  app/routers/           엔드포인트. auth·users·admin(박동현), airspace(임태헌), weather·suitability(윤지훈)
  app/models/            SQLAlchemy 모델
  app/schemas/           Pydantic 요청·응답 스키마
  app/services/          외부 API 호출, Pandas 가공, 적합도 계산 등 비즈니스 로직
  scripts/               공역 데이터 수집·변환 일회성 스크립트 (임태헌)
  tests/
data/raw/   원본 데이터 (git 제외)   data/sample/  소량 샘플만 커밋
docs/       ERD, API 명세, 회의록
```

규칙:
- **폴더·파일을 임의로 이동하거나 이름을 바꾸지 않는다.** 구조 변경은 두 팀장 합의 후에만 한다.
- **자기 담당 영역만 수정한다.** 다른 사람 담당 파일을 고쳐야 하면 수정하지 말고 사용자에게 알린다.
- 새 파일은 위 구조의 알맞은 폴더에 만든다. 새 최상위 폴더를 만들지 않는다.

## 4. 보안 (절대 규칙)

- `.env`, API 키, DB 비밀번호, Oracle Wallet 파일을 **코드·커밋·채팅 출력에 넣지 않는다.** 값은 항상 환경변수로 읽는다.
- 새 환경변수를 쓰면 키 이름만 `.env.example`에 추가한다 (값은 비움).
- **기상청 등 외부 API 키는 백엔드에서만 사용한다.** 프론트에서 직접 호출하지 않는다.
  프론트에 두는 키는 VWorld 키(`VITE_VWORLD_KEY`)뿐이다.
- 비밀번호는 반드시 해시(bcrypt 등)로 저장한다. 평문 저장·로그 출력 금지.
- 모든 보호 API는 서버에서 인증·권한(일반 회원/관리자)을 검사한다. 프론트 검사만 믿지 않는다.
- SQL은 SQLAlchemy 파라미터 바인딩만 쓴다. 문자열 이어붙이기로 쿼리를 만들지 않는다.
- 이미 비밀 정보가 커밋된 것을 발견하면 즉시 사용자에게 알린다 (키 재발급 필요).

## 5. 백엔드 규칙 (FastAPI)

- 계층: `routers`(요청·응답만) → `services`(로직) → `models`(DB). 라우터에 비즈니스 로직을 쓰지 않는다.
- 모든 엔드포인트는 `/api` 접두사를 쓰고, 요청·응답은 `schemas`의 Pydantic 모델로 정의한다.
- 외부 API 호출(`requests`)에는 timeout을 넣고, 실패 시 의미 있는 에러 응답을 돌려준다.
- 기능마다 별도 파일을 쓴다 (한 라우터 파일에 여러 사람의 기능을 섞지 않는다).
- 엔드포인트를 추가·변경하면 `docs/`의 API 명세도 함께 갱신한다.

## 6. 프론트 규칙 (React + TypeScript)

- TypeScript strict. `any` 사용 금지. API 응답은 `src/types/`에 타입을 정의한다.
- 서버 호출은 `src/api/`의 함수로만 하고, 컴포넌트에서 `fetch`를 직접 쓰지 않는다.
- OpenLayers·VWorld 관련 코드는 `src/features/map/` 안에서만 다룬다.
- 환경변수는 `import.meta.env.VITE_*`로 읽는다. 키를 코드에 하드코딩하지 않는다.
- 색상·간격은 `src/styles/`의 토큰을 쓴다 (네이비·블루·화이트). PC·모바일 반응형을 지킨다.
- 로그인 여부에 따라 메뉴가 달라지는 것을 고려한다.

## 7. Git 규칙

- `main`, `develop`에 직접 push하지 않는다. `feature/<영역>-<기능>` 브랜치에서 작업 후 PR.
  예: `feature/front-map-layer`, `feature/back-auth`
- PR 승인: `frontend/` 변경은 이태용, `backend/` 변경은 윤지훈. 양쪽을 건드리면 두 팀장 모두.
- 커밋 메시지: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:` 말머리 + 한 줄 요약.
  예: `feat: 지도 공역 레이어 추가`
- 커밋 전에 `git status`로 `.env`, 원본 데이터, `node_modules` 등이 포함되지 않았는지 확인한다.
- `git push --force`, `git reset --hard` 등 되돌리기 어려운 명령은 사용자 확인 없이 실행하지 않는다.
- 한 PR에는 한 가지 목적만 담는다. 관련 없는 포맷팅·리팩터링을 섞지 않는다.

## 8. 데이터

- `data/raw/`(공역 원본 shp, 대용량 파일)는 커밋하지 않는다.
- 공역 데이터의 이용 조건(상업적 이용 등)은 확인 전이다. 출처와 라이선스를 `docs/`에 기록한다.
- 공유할 가공 결과가 크면 커밋하지 말고 팀에 방법을 문의한다.

## 9. AI 작업 방식

- 요청받은 범위만 수정한다. 요청하지 않은 기능, 추상화, 파일을 추가하지 않는다.
- 코드를 수정하기 전에 관련 파일을 먼저 읽고, 기존 코드의 이름·스타일을 따른다.
- 이미 있는 함수·타입·컴포넌트가 있으면 새로 만들지 않고 재사용한다.
- 커밋·push는 사용자가 요청할 때만 한다.
