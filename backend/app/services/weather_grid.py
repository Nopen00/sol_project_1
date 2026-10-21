import math


def latlon_to_grid(latitude: float, longitude: float) -> tuple[int, int]:
    """위도·경도를 기상청 단기예보 격자(nx, ny)로 변환합니다."""

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 < latitude < 90
        and -180 <= longitude <= 180
    ):
        raise ValueError("올바른 위도와 경도를 입력해 주세요.")

    re = 6371.00877 / 5.0
    rad = math.pi / 180.0

    slat1 = 30.0 * rad
    slat2 = 60.0 * rad
    olon = 126.0 * rad
    olat = 38.0 * rad

    xo = 43.0
    yo = 136.0

    sn = math.log(math.cos(slat1) / math.cos(slat2))
    sn /= math.log(
        math.tan(math.pi / 4 + slat2 / 2)
        / math.tan(math.pi / 4 + slat1 / 2)
    )

    sf = (
        math.tan(math.pi / 4 + slat1 / 2) ** sn
        * math.cos(slat1)
        / sn
    )

    ro = re * sf / math.tan(math.pi / 4 + olat / 2) ** sn
    ra = re * sf / math.tan(math.pi / 4 + latitude * rad / 2) ** sn

    theta = longitude * rad - olon

    if theta > math.pi:
        theta -= 2 * math.pi
    elif theta < -math.pi:
        theta += 2 * math.pi

    theta *= sn

    nx = math.floor(ra * math.sin(theta) + xo + 0.5)
    ny = math.floor(ro - ra * math.cos(theta) + yo + 0.5)

    if not (1 <= nx <= 149 and 1 <= ny <= 253):
        raise ValueError("기상청 단기예보 격자 영역 밖입니다.")

    return nx, ny
