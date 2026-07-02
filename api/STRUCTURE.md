# ERPulse API - 파일 구조

**생성일:** 2026-07-02  
**단계:** Phase 3 - FastAPI 앱 기본 뼈대

---

## 루트 파일

| 파일 | 설명 |
|------|------|
| `requirements.txt` | Python 패키지 목록 (FastAPI, SQLAlchemy, Redis, httpx 등) |
| `.env.example` | 환경변수 템플릿 (`.env`로 복사 후 값 채워서 사용) |
| `Dockerfile` | python:3.12-slim 기반 컨테이너 이미지 빌드 설정 |
| `docker-compose.yml` | 로컬 테스트용 구성 (api + PostgreSQL 16 + Redis 7) |
| `alembic.ini` | Alembic 마이그레이션 설정 파일 |

---

## app/

| 파일 | 설명 |
|------|------|
| `app/main.py` | FastAPI 앱 진입점. 라우터 등록, lifespan(Redis 종료 처리) |
| `app/config.py` | pydantic-settings 기반 환경변수 관리 (DATABASE_URL, REDIS_URL, API 키 등) |
| `app/database.py` | SQLAlchemy 비동기 엔진 및 세션 팩토리, `Base` 클래스 정의 |
| `app/redis_client.py` | Redis 싱글턴 클라이언트. `get_redis()` / `close_redis()` |
| `app/models.py` | `Hospital` DB 모델 (hpid, 병원명, 주소, 전화번호, 가용 병상 수 등) |
| `app/schemas.py` | Pydantic 응답 스키마 (`HospitalResponse`, `HealthResponse`) |

---

## app/routers/

| 파일 | 설명 |
|------|------|
| `app/routers/hospitals.py` | 응급실 API 라우터 (`GET /hospitals`, `/hospitals/realtime`, `/hospitals/{hpid}`) |

---

## app/services/

| 파일 | 설명 |
|------|------|
| `app/services/collector.py` | 공공데이터포털 응급의료 API 호출 (`getEgytListInfoInqire`, `getEmrrmRltmUsefulSckbdInfoInqire`) |
| `app/services/fallback.py` | Redis TTL Fallback 로직. 캐시 hit 시 Redis 반환, miss 시 API 호출 후 캐싱 |

---

## alembic/

| 파일 | 설명 |
|------|------|
| `alembic/env.py` | 비동기 SQLAlchemy 엔진 기반 마이그레이션 실행 환경 설정 |
| `alembic/script.py.mako` | 마이그레이션 파일 자동 생성 템플릿 |
| `alembic/versions/001_initial.py` | 초기 마이그레이션 - `hospitals` 테이블 생성 |
