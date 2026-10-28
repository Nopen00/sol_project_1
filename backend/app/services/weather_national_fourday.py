
from datetime import datetime, timedelta, time

from backend.app.services.weather_forecast import KST


def build_forecast_times(now):
    # 오늘을 포함한 4일간의 마지막 날짜
    last_day = now.date() + timedelta(days=3)

    # 현재 이후 첫 정시
    current = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(hours=1)

    # 마지막 날 23시까지
    end = datetime.combine(
        last_day,
        time(23, 0),
        tzinfo=KST,
    )

    times = []

    while current <= end:
        times.append(current)
        current += timedelta(hours=1)

    return times


def main():
    now = datetime.now(KST)
    times = build_forecast_times(now)

    print("===== 전국 4일 예보 수집 계획 =====")
    print("현재 시각:", now.strftime("%Y-%m-%d %H:%M"))
    print("시작 날짜:", now.date())
    print("마지막 날짜:", now.date() + timedelta(days=3))
    print("후보 예보 시각 수:", len(times))

    print("\n날짜별 조회 후보")

    for offset in range(4):
        day = now.date() + timedelta(days=offset)
        count = sum(t.date() == day for t in times)
        print(f"{day}: {count}개")

    if times:
        print("\n첫 예보:", times[0])
        print("마지막 예보:", times[-1])

    print("\nAPI 호출 없음 / Oracle 변경 없음")


if __name__ == "__main__":
    main()
