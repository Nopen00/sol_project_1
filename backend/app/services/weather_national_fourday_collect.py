
import argparse
import subprocess
import sys

from datetime import datetime, timedelta, time
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from backend.app.services.weather_forecast import KST, load_env
from backend.app.services.weather_national_fourday import (
    build_forecast_times,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def cleanup_old_weather():
    env = load_env()

    if env.get("DB_HOST") not in ("localhost", "127.0.0.1"):
        raise RuntimeError("로컬 실습 DB가 아닙니다.")

    if env.get("DB_USER", "").upper() != "DRONE_APP":
        raise RuntimeError("실습용 DB 계정이 아닙니다.")

    # 어제 00:00 이전 데이터 삭제 (한국 시간 기준)
    now = datetime.now(KST)
    yesterday = now.date() - timedelta(days=1)
    cutoff = datetime.combine(yesterday, time.min)

    db_url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={"service_name": env["DB_SERVICE"]},
    )

    engine = create_engine(db_url)

    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM WEATHER_NATIONAL_FORECAST_PRACTICE
                    WHERE FORECAST_AT < :cutoff
                """),
                {"cutoff": cutoff},
            )

        print("오래된 날씨 삭제 기준:", cutoff)
        print("삭제된 행:", result.rowcount)

    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--all",
        action="store_true",
        help="4일치 전체 수집",
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Oracle에 실제 저장",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=2,
        help="테스트할 예보 시각 개수",
    )

    parser.add_argument(
        "--hourly",
        action="store_true",
        help="3시간 간격 대신 1시간 간격 수집",
    )

    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit은 1 이상이어야 합니다.")

    now = datetime.now(KST)

    # 기본은 3시간 간격 예보
    all_times = build_forecast_times(now)

    if args.hourly:
        times = all_times
    else:
        times = [
            t for t in all_times
            if t.hour % 3 == 0
        ]

    selected = times if args.all else times[:args.limit]

    print("===== 전국 4일 날씨 자동 수집 =====", flush=True)
    print("시작 시각:", now, flush=True)
    print("수집 간격:", "1시간" if args.hourly else "3시간")
    print("수집 대상 시각:", len(selected))
    print("Oracle 저장:", args.save, flush=True)

    success = 0
    failed_times = []

    for index, forecast_time in enumerate(selected, start=1):
        print(
            f"\n[{index}/{len(selected)}] "
            f"{forecast_time:%Y-%m-%d %H:%M}",
            flush=True,
        )

        command = [
            sys.executable,
            "-m",
            "backend.app.services.weather_national_bulk_save",
            "--forecast-at",
            forecast_time.strftime("%Y-%m-%dT%H:%M"),
        ]

        if args.save:
            command.append("--save")

        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        output = (
            (result.stdout or "")
            + "\n"
            + (result.stderr or "")
        )

        if result.returncode == 0:
            success += 1
            print("수집 성공")

            for line in output.splitlines():
                if line.startswith((
                    "저장 대상 격자:",
                    "변경된 행:",
                    "테이블 전체 행:",
                )):
                    print(line)

        else:
            failed_times.append(forecast_time)
            print("수집 실패")

            # 오류 확인에 필요한 마지막 로그만 출력
            print("\n".join(output.splitlines()[-12:]))

    print("\n===== 전체 수집 결과 =====")
    print("성공:", success)
    print("실패:", len(failed_times))

    for failed_time in failed_times:
        print("실패한 시각:", failed_time)

    # 전체 수집 및 저장 성공 시에만 자동 삭제
    if args.save and args.all and not failed_times:
        print("\n===== 오래된 날씨 자동 삭제 =====")
        cleanup_old_weather()

    if not args.save:
        print("Oracle DB 변경 없음")

    if failed_times:
        raise SystemExit(1)

    print("\n전국 날씨 수집 작업 완료!")


if __name__ == "__main__":
    main()
