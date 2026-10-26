"""전국 날씨 수집용 디스크 용량 및 실행시간 보호."""

import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

WARN_PERCENT = 80
STOP_PERCENT = 90
MAX_SECONDS = 3600
CHECK_SECONDS = 30

PROJECT = "/opt/sol_project_1"

COMMAND = [
    f"{PROJECT}/backend/.venv/bin/python",
    "-u",
    "-m",
    "backend.app.services.weather_national_v2_collect",
    "--all",
    "--save",
]


def log(message):
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[{now}] {message}", flush=True)


def disk_percent():
    total, used, free = shutil.disk_usage("/")
    return used * 100 / total


def main():
    usage = disk_percent()
    log(f"디스크 사용률: {usage:.1f}%")

    if usage >= STOP_PERCENT:
        log("ERROR: 디스크 90% 이상. 날씨 수집 차단")
        return 2

    if usage >= WARN_PERCENT:
        log("WARNING: 디스크 80% 이상")

    # Oracle 저장 할당량 검사
    log("Oracle 저장 할당량 확인")

    try:
        quota = subprocess.run(
            [
                f"{PROJECT}/backend/.venv/bin/python",
                "-u",
                "-m",
                "backend.app.services.weather_quota_guard",
            ],
            cwd=PROJECT,
            timeout=45,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"ERROR: Oracle 할당량 검사 실패 ({type(exc).__name__})")
        return 2

    if quota.returncode != 0:
        log("ERROR: Oracle 할당량 부족 또는 검사 오류. 수집 차단")
        return 2

    if "--check" in sys.argv:
        log("보호 기능 점검 완료. 실제 수집하지 않음")
        return 0

    log("전국 날씨 수집 시작")
    process = subprocess.Popen(
        COMMAND,
        cwd=PROJECT,
        start_new_session=True,
    )
    started = time.monotonic()
    warned = usage >= WARN_PERCENT

    while process.poll() is None:
        usage = disk_percent()
        elapsed = time.monotonic() - started

        if usage >= STOP_PERCENT or elapsed >= MAX_SECONDS:
            reason = (
                "디스크 사용률 90% 도달"
                if usage >= STOP_PERCENT
                else "수집 실행시간 60분 초과"
            )
            log(f"ERROR: {reason}. 종료 요청")
            os.killpg(process.pid, signal.SIGTERM)

            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                log("ERROR: 정상 종료 지연. 수집 프로세스 강제 종료")
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()

            return 2

        if usage >= WARN_PERCENT and not warned:
            log(f"WARNING: 디스크 사용률 {usage:.1f}%")
            warned = True

        time.sleep(CHECK_SECONDS)

    log(f"수집 종료. 반환 코드: {process.returncode}")
    return process.returncode


if __name__ == "__main__":
    sys.exit(main())
