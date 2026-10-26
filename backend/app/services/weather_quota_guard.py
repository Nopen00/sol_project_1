"""Oracle DRONE_APP 저장 할당량 점검."""

from sqlalchemy import text

from backend.app.services.weather_forecast import load_env
from backend.app.services.weather_national_v2_collect import engine_for


def main():
    engine = engine_for(load_env())

    try:
        with engine.connect() as conn:
            username = conn.execute(
                text("SELECT USER FROM DUAL")
            ).scalar_one()

            if username.upper() != "DRONE_APP":
                print("ERROR: DB 연결 계정이 DRONE_APP이 아닙니다.")
                return 2

            rows = conn.execute(text("""
                SELECT TABLESPACE_NAME, BYTES, MAX_BYTES
                FROM USER_TS_QUOTAS
            """)).all()

        if not rows:
            print("ERROR: Oracle 할당량 정보를 확인할 수 없습니다.")
            return 2

        blocked = False

        for name, used, limit in rows:
            if limit == -1:
                print(f"{name}: UNLIMITED 할당량")
                continue

            if limit <= 0:
                print(f"ERROR: {name} 저장 할당량 없음")
                blocked = True
                continue

            percent = used / limit * 100

            print(
                f"{name}: {used / 1024**2:.1f}MB / "
                f"{limit / 1024**2:.1f}MB "
                f"({percent:.1f}%)",
                flush=True,
            )

            if percent >= 90:
                print("ERROR: Oracle 할당량 90% 이상")
                blocked = True
            elif percent >= 80:
                print("WARNING: Oracle 할당량 80% 이상")

        return 2 if blocked else 0

    except Exception as exc:
        print(
            f"ERROR: Oracle 할당량 검사 실패 "
            f"({type(exc).__name__})"
        )
        return 2

    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
