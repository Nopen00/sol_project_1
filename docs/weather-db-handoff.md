# 날씨 데이터 및 Oracle DB 인수인계

## 1. 담당 범위

이 코드는 기상청 날씨 데이터를 수집하고 Oracle DB에 저장합니다.

FastAPI 엔드포인트, 비행 적합도 계산, 프론트엔드 화면은 별도 담당자가 구현합니다.

## 2. 운영 환경

- 서버: 가비아 Ubuntu
- DB: Oracle FREEPDB1
- 테이블 소유자: DRONE_APP
- 실행 경로: /opt/sol_project_1
- 서버 Python: backend/.venv/bin/python
- API 인증정보: backend/.env (Git 제외)

## 3. Python 실행 파일

- weather_national_v2_collect.py
  - 전국 미래 예보 수집 및 Oracle 저장
  - 전체 수집 성공 후 오래된 예보 정리

- weather_current_v2_collect.py
  - 지정한 NX, NY 격자의 현재 날씨 조회 및 저장

- weather_national_save.py
  - 기상청 전국 격자 API 호출

- weather_forecast.py
  - 환경변수 로드 및 발표 시각 관련 공통 함수

네 파일 모두 backend/app/services/에 있습니다.

## 4. 필요한 패키지

- requests
- SQLAlchemy
- oracledb (Oracle Python 드라이버)

설치 전 팀 프로젝트 의존성 승인 규칙을 따릅니다.

## 5. 환경변수

backend/.env.example을 참고합니다.

DB_HOST
DB_PORT
DB_SERVICE
DB_USER
DB_PASSWORD
KMA_HUB_KEY
KMA_SERVICE_KEY

실제 비밀번호 및 API 키는 GitHub에 올리지 않습니다.

## 6. Oracle 테이블

DRONE_MODEL_SPECS
- 드론 14종 사양 및 프로젝트 평가 기준

WEATHER_NATIONAL_FORECAST_V2
- 전국 격자별 미래 예보
- 기온, 풍속, 풍향, 강수 관련 원본 데이터

WEATHER_CURRENT_OBS_V2
- 지정 격자의 현재 관측 데이터

WEATHER_COLLECTION_RUNS_V2
- 전국 예보 수집 작업 기록

기존 PRACTICE 테이블은 수정하지 않습니다.

## 7. 수동 실행

프로젝트 루트에서 실행합니다.

미래 예보 1개 시각 저장:
backend/.venv/bin/python -m backend.app.services.weather_national_v2_collect --limit 1 --save

미래 예보 전체 수집:
backend/.venv/bin/python -m backend.app.services.weather_national_v2_collect --all --save --cleanup

현재 날씨 격자 조회 및 저장:
backend/.venv/bin/python -m backend.app.services.weather_current_v2_collect --nx 60 --ny 127 --save

## 8. 자동 갱신

가비아 서버 cron에 전국 예보 자동 갱신을 등록했습니다.

주기: 매일 00:50부터 3시간 간격 (KST)
중복 실행 방지: flock
실행 로그: backend/logs/forecast_cron.log

cron 등록은 Git 저장소에 자동으로 포함되지 않습니다.
새 서버 배포 시 별도 설정이 필요합니다.

최초 전국 예보 수집 59/59 성공.
실제 cron 예약 실행 성공 여부는 별도 로그 검증이 필요합니다.

## 9. DB 조회 예시

전국 예보:
SELECT FORECAST_AT, TEMPERATURE_C,
       WIND_SPEED_MS, WIND_DIRECTION_DEG,
       PTY_RAW, PCP_RAW, POP_RAW
FROM WEATHER_NATIONAL_FORECAST_V2
WHERE NX = 60 AND NY = 127
ORDER BY FORECAST_AT
FETCH FIRST 10 ROWS ONLY;

현재 관측:
SELECT OBSERVED_AT, TEMPERATURE_C,
       WIND_SPEED_MS, WIND_DIRECTION_DEG,
       PTY_RAW, RN1_AMOUNT_MM
FROM WEATHER_CURRENT_OBS_V2
WHERE NX = 60 AND NY = 127
ORDER BY OBSERVED_AT DESC
FETCH FIRST 1 ROW ONLY;

드론 목록:
SELECT BRAND, MODEL_NAME, EVALUATION_WIND_MS
FROM DRONE_MODEL_SPECS
ORDER BY BRAND, MODEL_NAME;

## 10. 주의 사항

- DB 데이터는 가비아 Oracle에 저장되어 있으며 Git에는 포함하지 않습니다.
- 사용자별 Oracle 접근 권한은 별도로 설정해야 합니다.
- 현재 날씨는 요청한 격자를 수집하는 방식입니다.
- 미래 예보의 원본 강수 코드와 단위는 검증 상태를 확인해야 합니다.
- POP 원본값을 검증 없이 강수확률(%)로 해석하지 않습니다.
- 드론 사양 중 REVIEW_REQUIRED는 공식 사양 재확인이 필요합니다.
- 비행 적합도는 참고용이며 공식 비행 승인과 다릅니다.
