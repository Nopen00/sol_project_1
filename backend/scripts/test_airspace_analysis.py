
from app.services.airspace_analysis import analyze_airspace

# 테스트 1: 비행금지구역(P)
p_data = {
    "features": [
        {"properties": {"airspace_type": "P"}}
    ]
}

# 테스트 2: 비행제한구역(R)
r_data = {
    "features": [
        {"properties": {"airspace_type": "R"}}
    ]
}

# 테스트 3: 조회된 P/R 공역 없음
empty_data = {
    "features": []
}

print("P 구역:", analyze_airspace(p_data))
print("R 구역:", analyze_airspace(r_data))
print("조회 결과 없음:", analyze_airspace(empty_data))
