"# sol_project_1" 
# 🚁 드론 비행 공역 및 기상 적합도 분석 서비스

드론 비행 위치의 공역 정보와 기상 조건을 분석하여 비행 적합도를 안내하는 웹서비스입니다.

## 1. 주요 기능

- 카카오맵에서 위치 선택
- 비행금지구역(P) 및 비행제한구역(R) 조회
- 드론 기종 선택
- 선택한 위치의 풍속·기온·강수 분석
- 드론 기종별 비행 적합도 평가

> 비행 적합도는 참고용 정보입니다. 실제 드론 비행 전에는 최신 공식 공역 정보와 비행 승인 요건을 확인해야 합니다.

## 2. 기술 스택

| 구분 | 기술 |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | Oracle Database |
| 지도 | Kakao Maps API |
| 날씨 | 기상청 API |
| DB 관리 | DBeaver |
| 협업 | Git, GitHub |

## 3. 사전 설치 프로그램

프로젝트 실행 전에 다음 프로그램을 설치합니다.

- Git
- Python
- Node.js 및 npm
- VS Code
- DBeaver (DB 확인이 필요한 경우)

Python과 Node.js 버전은 팀에서 사용하는 버전으로 통일하는 것을 권장합니다.

## 4. 프로젝트 다운로드

터미널에서 실행합니다.

```bash
git clone https://github.com/Nopen00/sol_project_1.git
cd sol_project_1
```

## 5. Python 가상환경 설정

프로젝트 최상위 폴더에서 실행합니다.

Windows PowerShell 기준:

```powershell
python -m venv .venv
```

가상환경의 Python을 사용하여 필요한 라이브러리를 설치합니다.

```powershell
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

**참고:** `backend/requirements.txt` 파일이 저장소에 있어야 합니다. 아직 없다면 백엔드 담당자가 실제 사용 중인 의존성을 정리해 추가해야 합니다.

## 6. 환경변수 설정

`backend` 폴더에 `.env` 파일을 생성합니다.

```env
DB_USER=팀에서_발급받은_DB계정
DB_PASSWORD=팀에서_발급받은_DB비밀번호
DB_HOST=127.0.0.1
DB_PORT=11522
DB_SERVICE=FREEPDB1

KMA_HUB_KEY=발급받은_API키
KMA_SERVICE_KEY=발급받은_API키
```

실제 값은 팀 담당자에게 확인합니다.

프론트엔드의 환경변수 파일도 설정합니다.

`frontend/.env`

```env
VITE_KAKAO_MAP_KEY=발급받은_카카오맵_JavaScript키
```

**주의:** `.env` 파일은 비밀번호와 API 키가 포함되므로 GitHub에 업로드하지 않습니다. `.gitignore`에 등록해야 합니다.

## 7. Oracle DB SSH 연결

현재 팀에서 사용하는 SSH 터널 방식입니다.

별도 터미널을 열고 실행합니다.

```powershell
ssh -N -L 11522:127.0.0.1:1521 team04@1.201.112.78
```

SSH 인증을 완료한 뒤 해당 터미널을 종료하지 않습니다.

이 설정은 현재 팀 서버 기준이며, 서버 주소·계정·접속 권한이 변경되면 팀 담당자에게 확인해야 합니다.

## 8. FastAPI 백엔드 실행

프로젝트 최상위 폴더에서 실행합니다.

```powershell
.venv\Scripts\python.exe -m uvicorn test_airspace_main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```

백엔드 주소:

http://127.0.0.1:8001

API 문서:

http://127.0.0.1:8001/docs

## 9. React 프론트엔드 실행

새 터미널에서 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

PowerShell 실행 정책으로 `npm` 실행이 막히면 다음 명령어를 사용합니다.

```powershell
npm.cmd run dev
```

프론트엔드 주소:

http://localhost:5173

비행 적합도 페이지:

http://localhost:5173/map/suitability

## 10. 실행 순서 요약

1. GitHub에서 프로젝트 다운로드
2. Python 가상환경 생성 및 라이브러리 설치
3. 프론트엔드 라이브러리 설치
4. 환경변수 설정
5. SSH 터널 실행 및 유지
6. FastAPI 서버 실행
7. React 개발 서버 실행
8. 브라우저에서 웹사이트 접속

## 11. 주요 API

| API | 기능 |
|---|---|
| `GET /drones` | 드론 목록 조회 |
| `GET /flight-analysis` | 기상 기반 비행 적합도 분석 |
| `GET /airspace` | 위치별 공역 조회 |
| `GET /airspace/analysis` | 공역 분석 |

비행 적합도 요청 예시:

```text
GET /flight-analysis?model_id=AUTEL_EVO_LITE&latitude=37.5665&longitude=126.9780
```

## 12. 주의사항

- 프론트엔드와 백엔드 서버를 모두 실행해야 합니다.
- DB 조회 기능에는 SSH 터널 연결이 필요합니다.
- API 키와 비밀번호는 GitHub에 업로드하지 않습니다.
- 강수 데이터 검증 및 비행 안전 판단 로직은 추가 보완이 필요합니다.
- 기상 적합도가 양호해도 법적으로 비행이 허용된다는 의미는 아닙니다.
