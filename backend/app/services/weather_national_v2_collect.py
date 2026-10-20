
"""SOL_PROJECT_1 전국 단기예보 수집 및 Oracle 저장."""

import argparse
import math
import re
import time as clock
import uuid
from datetime import datetime, timedelta, time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from backend.app.services.weather_forecast import (
    KST,
    get_base_datetime,
    load_env,
)
from backend.app.services.weather_national_save import fetch_grid


SOURCE = "nph-dfs_shrt_grd"
CATEGORIES = ("TMP", "WSD", "VEC", "PTY", "PCP", "POP")
GRID_X = 149
GRID_Y = 253
BATCH_SIZE = 2000


MERGE = text("""
MERGE INTO WEATHER_NATIONAL_FORECAST_V2 t
USING (
 SELECT :source_api source_api, :nx nx, :ny ny,
        :forecast_at forecast_at FROM DUAL
) s
ON (
 t.SOURCE_API=s.source_api
 AND t.NX=s.nx
 AND t.NY=s.ny
 AND t.FORECAST_AT=s.forecast_at
)
WHEN MATCHED THEN UPDATE SET
 t.ISSUED_AT=:issued_at,
 t.TEMPERATURE_C=:temperature_c,
 t.WIND_SPEED_MS=:wind_speed_ms,
 t.WIND_DIRECTION_DEG=:wind_direction_deg,
 t.PTY_RAW=:pty_raw,
 t.PTY_NORMALIZED=:pty_normalized,
 t.PCP_RAW=:pcp_raw,
 t.PCP_AMOUNT_MM=:pcp_amount_mm,
 t.POP_RAW=:pop_raw,
 t.POP_PROBABILITY_PCT=:pop_probability_pct,
 t.PTY_STATUS=:pty_status,
 t.PCP_STATUS=:pcp_status,
 t.POP_STATUS=:pop_status,
 t.DATA_QUALITY_FLAGS=:data_quality_flags,
 t.FETCHED_AT=LOCALTIMESTAMP
WHERE t.ISSUED_AT < :issued_at AND :complete_row=1
WHEN NOT MATCHED THEN INSERT (
 SOURCE_API,NX,NY,FORECAST_AT,ISSUED_AT,
 TEMPERATURE_C,WIND_SPEED_MS,WIND_DIRECTION_DEG,
 PTY_RAW,PTY_NORMALIZED,PCP_RAW,PCP_AMOUNT_MM,
 POP_RAW,POP_PROBABILITY_PCT,
 PTY_STATUS,PCP_STATUS,POP_STATUS,DATA_QUALITY_FLAGS
) VALUES (
 :source_api,:nx,:ny,:forecast_at,:issued_at,
 :temperature_c,:wind_speed_ms,:wind_direction_deg,
 :pty_raw,:pty_normalized,:pcp_raw,:pcp_amount_mm,
 :pop_raw,:pop_probability_pct,
 :pty_status,:pcp_status,:pop_status,:data_quality_flags
)
""")


INSERT_LOG = text("""
INSERT INTO WEATHER_COLLECTION_RUNS_V2 (
 RUN_ID,JOB_TYPE,STARTED_AT,FINISHED_AT,
 FORECAST_START_AT,FORECAST_END_AT,ISSUED_AT,
 EXPECTED_SLOTS,SUCCESS_SLOTS,API_REQUESTS,
 ROWS_MERGED,RUN_STATUS
) VALUES (
 :run_id,:job_type,:started_at,:finished_at,
 :first_at,:last_at,:issued_at,
 :expected,:success,:requests,:changed,:status
)
""")


FINISH_LOG = text("""
UPDATE WEATHER_COLLECTION_RUNS_V2
SET FINISHED_AT=:finished_at,
 SUCCESS_SLOTS=:success,
 API_REQUESTS=:requests,
 ROWS_MERGED=:changed,
 RUN_STATUS=:status,
 ERROR_MESSAGE=:message
WHERE RUN_ID=:run_id
""")


ALREADY_DONE = text("""
SELECT COUNT(*)
FROM WEATHER_COLLECTION_RUNS_V2
WHERE ISSUED_AT=:issued_at
 AND FORECAST_START_AT=:forecast_at
 AND FORECAST_END_AT=:forecast_at
 AND RUN_STATUS='SUCCESS'
 AND (
  JOB_TYPE='FORECAST_SLOT'
  OR (
   JOB_TYPE='NATIONAL_FORECAST'
   AND EXPECTED_SLOTS=1
  )
 )
""")


def slots_for_publication(now, base):
    """기상청 공식 제공 범위의 모든 미래 정시 예보."""

    if base.hour in (2, 5, 8, 11, 14):
        extra_days = 3
    else:
        extra_days = 4

    last = datetime.combine(
        base.date() + timedelta(days=extra_days),
        time(0, 0),
        tzinfo=KST,
    )

    first = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    if first <= now:
        first += timedelta(hours=1)

    result = []

    while first <= last:
        result.append(first)
        first += timedelta(hours=1)

    return result


def numeric(value):
    if value is None:
        return None

    number = float(value)

    if not math.isfinite(number) or number <= -99:
        return None

    return number


def make_records(grids, base, slot):
    expected = GRID_X * GRID_Y

    for category in CATEGORIES:
        if category not in grids:
            raise RuntimeError("기상요소 누락: " + category)

        if len(grids[category]) != expected:
            raise RuntimeError("전국 격자 개수 오류")

    rows = []
    full_count = 0

    for i in range(expected):
        values = {
            cat: numeric(grids[cat][i])
            for cat in CATEGORIES
        }

        if all(v is None for v in values.values()):
            continue

        ny, x = divmod(i, GRID_X)

        wind = values["WSD"]
        if wind is not None and wind < 0:
            wind = None

        direction = values["VEC"]
        if direction is not None and not 0 <= direction <= 360:
            direction = None

        pty = values["PTY"]
        pcp = values["PCP"]
        pop = values["POP"]

        complete = all(
            v is not None for v in (
                values["TMP"],
                wind,
                direction,
                pty,
                pcp,
                pop,
            )
        )

        full_count += int(complete)

        rows.append({
            "source_api": SOURCE,
            "nx": x + 1,
            "ny": ny + 1,
            "forecast_at": slot.replace(tzinfo=None),
            "issued_at": base.replace(tzinfo=None),
            "temperature_c": values["TMP"],
            "wind_speed_ms": wind,
            "wind_direction_deg": direction,
            "pty_raw": None if pty is None else format(pty, ".15g"),
            "pty_normalized": None,
            "pcp_raw": None if pcp is None else format(pcp, ".15g"),
            "pcp_amount_mm": None,
            "pop_raw": None if pop is None else format(pop, ".15g"),
            "pop_probability_pct": None,
            "pty_status": "RAW_UNVERIFIED" if pty is not None else "MISSING",
            "pcp_status": "RAW_UNVERIFIED" if pcp is not None else "MISSING",
            "pop_status": "RAW_UNVERIFIED" if pop is not None else "MISSING",
            "data_quality_flags": (
                "CODE_MEANING_UNVERIFIED"
                if complete
                else "MISSING_SOURCE_VALUE;CODE_MEANING_UNVERIFIED"
            ),
            "complete_row": int(complete),
        })

    return rows, full_count


def engine_for(env):
    if (
        env.get("DB_USER", "").upper() != "DRONE_APP"
        or env.get("DB_HOST") not in ("localhost", "127.0.0.1")
    ):
        raise RuntimeError("로컬 DRONE_APP DB만 허용합니다.")

    url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={"service_name": env["DB_SERVICE"]},
    )

    engine = create_engine(url)

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT USER FROM DUAL")
        ).scalar_one()

        if str(user).upper() != "DRONE_APP":
            raise RuntimeError("Oracle 계정 확인 실패")

        found = set(
            conn.execute(
                text("SELECT TABLE_NAME FROM USER_TABLES")
            ).scalars()
        )

        required = {
            "WEATHER_NATIONAL_FORECAST_V2",
            "WEATHER_COLLECTION_RUNS_V2",
        }

        if not required.issubset(found):
            raise RuntimeError("필요한 Oracle 테이블이 없습니다.")

    return engine


def log_record(
    run_id, job, now, first, last, base,
    expected, success, requests, changed, status,
):
    return {
        "run_id": run_id,
        "job_type": job,
        "started_at": now.replace(tzinfo=None),
        "finished_at": (
            None if status == "RUNNING"
            else datetime.now(KST).replace(tzinfo=None)
        ),
        "first_at": first.replace(tzinfo=None),
        "last_at": last.replace(tzinfo=None),
        "issued_at": base.replace(tzinfo=None),
        "expected": expected,
        "success": success,
        "requests": requests,
        "changed": changed,
        "status": status,
    }


def safe_message(exc):
    if isinstance(exc, RuntimeError):
        return str(exc)[:120]

    match = re.search(r"ORA-\d{5}", str(exc))

    return type(exc).__name__ + (
        " " + match.group() if match else ""
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--cleanup", action="store_true")

    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit은 1 이상이어야 합니다.")

    if args.cleanup and not (args.all and args.save):
        parser.error("--cleanup은 --all --save와 함께 사용하세요.")

    now = datetime.now(KST)
    base = get_base_datetime(now)

    slots = slots_for_publication(now, base)

    chosen = slots if args.all else slots[:args.limit]

    if not chosen:
        raise SystemExit("조회 가능한 미래 예보가 없습니다.")

    env = load_env()

    if not env.get("KMA_HUB_KEY"):
        raise SystemExit("KMA_HUB_KEY가 없습니다.")

    print(
        f"발표: {base:%Y-%m-%d %H:%M}",
        flush=True,
    )

    print(
        f"최대 제공 시각: {slots[-1]:%Y-%m-%d %H:%M}",
        flush=True,
    )

    print(
        f"수집 예보: {len(chosen)}개 / 전체 {len(slots)}개",
        flush=True,
    )

    print("Oracle 저장:", args.save, flush=True)

    begin = clock.perf_counter()
    run_id = str(uuid.uuid4())

    engine = None
    success = 0
    skipped = 0
    request_count = 0
    changed = 0
    failures = []

    try:
        if args.save:
            engine = engine_for(env)

            with engine.begin() as conn:
                conn.execute(
                    INSERT_LOG,
                    log_record(
                        run_id,
                        "NATIONAL_FORECAST",
                        now,
                        chosen[0],
                        chosen[-1],
                        base,
                        len(chosen),
                        0, 0, 0,
                        "RUNNING",
                    ),
                )

        for pos, slot in enumerate(chosen, 1):
            print(
                f"\n[{pos}/{len(chosen)}] "
                f"{slot:%m-%d %H:%M}",
                flush=True,
            )

            started = clock.perf_counter()

            try:
                if args.save:
                    with engine.connect() as conn:
                        was_done = conn.execute(
                            ALREADY_DONE,
                            {
                                "issued_at": base.replace(tzinfo=None),
                                "forecast_at": slot.replace(tzinfo=None),
                            },
                        ).scalar_one()

                    if was_done:
                        skipped += 1
                        success += 1

                        print(
                            "이미 저장된 동일 발표 자료: 건너뜀",
                            flush=True,
                        )
                        continue

                grids = {}

                for category in CATEGORIES:
                    request_count += 1

                    grids[category] = fetch_grid(
                        env["KMA_HUB_KEY"],
                        base,
                        slot,
                        category,
                    )

                rows, complete = make_records(
                    grids,
                    base,
                    slot,
                )

                if not rows:
                    raise RuntimeError("전국 예보가 모두 결측입니다.")

                print(
                    f"유효 격자 {len(rows):,}개 "
                    f"/ 6종 완비 {complete:,}개",
                    flush=True,
                )

                if args.save:
                    per_slot = 0

                    with engine.begin() as conn:
                        for idx in range(
                            0,
                            len(rows),
                            BATCH_SIZE,
                        ):
                            batch = rows[idx:idx + BATCH_SIZE]

                            result = conn.execute(MERGE, batch)

                            per_slot += max(
                                0,
                                result.rowcount or 0,
                            )

                            processed = min(
                                idx + BATCH_SIZE,
                                len(rows),
                            )

                            print(
                                f"Oracle 저장 {processed:,}"
                                f"/{len(rows):,} "
                                f"({processed / len(rows) * 100:.0f}%) "
                                f"{clock.perf_counter() - started:.0f}초",
                                flush=True,
                            )

                        conn.execute(
                            INSERT_LOG,
                            log_record(
                                str(uuid.uuid4()),
                                "FORECAST_SLOT",
                                now,
                                slot,
                                slot,
                                base,
                                1, 1, 6,
                                per_slot,
                                "SUCCESS",
                            ),
                        )

                    changed += per_slot

                success += 1

                print(
                    f"시각 완료: "
                    f"{clock.perf_counter() - started:.1f}초",
                    flush=True,
                )

            except Exception as exc:
                err = safe_message(exc)

                failures.append(
                    f"{slot:%m-%d %H:%M} {err}"
                )

                print("실패:", err, flush=True)
                break

            elapsed = clock.perf_counter() - begin
            eta = elapsed / pos * (len(chosen) - pos)

            print(
                f"전체 {pos}/{len(chosen)} | "
                f"경과 {elapsed / 60:.1f}분 | "
                f"예상 남은 시간 {eta / 60:.1f}분",
                flush=True,
            )

        if args.save:
            with engine.begin() as conn:

                if (
                    args.cleanup
                    and not failures
                    and success == len(chosen)
                ):
                    cutoff = datetime.combine(
                        now.date(),
                        time.min,
                    )

                    deleted = conn.execute(
                        text("""
                            DELETE FROM WEATHER_NATIONAL_FORECAST_V2
                            WHERE FORECAST_AT < :cutoff
                        """),
                        {"cutoff": cutoff},
                    ).rowcount

                    print(
                        "지난 날짜 예보 정리:",
                        deleted,
                        flush=True,
                    )

                conn.execute(
                    FINISH_LOG,
                    {
                        "run_id": run_id,
                        "finished_at": datetime.now(
                            KST
                        ).replace(tzinfo=None),
                        "success": success,
                        "requests": request_count,
                        "changed": changed,
                        "status": (
                            "SUCCESS"
                            if not failures and success == len(chosen)
                            else "PARTIAL"
                        ),
                        "message": (
                            "; ".join(failures)[:1000]
                            if failures else None
                        ),
                    },
                )

                total = conn.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM WEATHER_NATIONAL_FORECAST_V2
                    """)
                ).scalar_one()

                print(
                    f"Oracle 총 저장 행: {total:,}",
                    flush=True,
                )

        print(
            f"\n성공: {success}/{len(chosen)}",
            flush=True,
        )

        print(
            f"이미 저장된 시각 생략: {skipped}",
            flush=True,
        )

        print(
            f"이번 DB 처리 행: {changed:,}",
            flush=True,
        )

        print(
            f"총 소요 시간: "
            f"{(clock.perf_counter() - begin) / 60:.1f}분",
            flush=True,
        )

        if failures:
            raise SystemExit(
                "오류로 중단했습니다. 기존 자료는 유지합니다."
            )

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
