# 날씨 API 개발 문서

## 1. 기능 설명

사용자가 입력한 위도와 경도를 기상청 격자 좌표로 변환한 뒤,
기상청 초단기실황 API에서 날씨 정보를 조회합니다.

## 2. 사용 기술

- Python 3.12
- FastAPI
- Pydantic
- requests
- 기상청 단기예보 조회서비스 (초단기실황)

## 3. API 명세

- Method: GET
- Endpoint: /api/weather

### 요청 파라미터

- latitude: 위도 (필수, 숫자)
- longitude: 경도 (필수, 숫자)

### 요청 예시

GET /api/weather?latitude=37.5665&longitude=126.9780

### 응답 예시

{
"latitude": 37.5665,
"longitude": 126.978,
"nx": 60,
"ny": 127,
"base_date": "20261014",
"base_time": "1100",
"temperature": "15.7",
"wind_speed": "3.1",
"wind_direction": "294",
"rainfall": "0"
}

### 응답 필드

- latitude, longitude: 요청 위치
- nx, ny: 기상청 격자 좌표
- base_date, base_time: 조회에 사용한 관측 기준 날짜와 시각
- temperature: 기온 (°C)
- wind_speed: 풍속 (m/s)
- wind_direction: 풍향 (도)
- rainfall: 1시간 강수량 (mm)

날씨 값은 현재 문자열로 반환하며,
데이터가 없으면 null이 반환될 수 있습니다.

### 응답 코드

- 200: 정상 조회
- 422: 잘못된 좌표 입력
- 502: 기상청 데이터 조회 실패

## 4. 테스트 결과

- 서울 및 인천 초단기실황 조회 성공
- 위도·경도 → 격자 좌표 변환 확인
- Swagger UI에서 HTTP 200 확인
- JSON 응답 형식 검증 완료

## 5. 환경 설정

- backend/.env에 KMA_SERVICE_KEY 설정 필요
- 실제 API 인증키는 Git에 업로드하지 않음

## 6. 현재 개발 범위

- 초단기실황 조회 기능 구현 완료
- 독립 테스트 서버에서 검증 완료
- 팀 공용 FastAPI 서버에는 아직 통합하지 않음

## 7. 향후 개발

- 초단기예보 및 단기예보 API 추가
- 비행 예정 시각별 날씨 조회
- 데이터 정규화 및 오류 처리 개선
- 프론트엔드 지도 연동
