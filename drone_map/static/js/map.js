
function initMap() {
    kakao.maps.load(async function () {

        // ========================================
        // 1. HTML 요소
        // ========================================

        const mapElement =
            document.getElementById("map");

        const statusElement =
            document.getElementById("status");

        const provinceSelect =
            document.getElementById("province-select");

        const citySelect =
            document.getElementById("city-select");

        const menuToggle =
            document.getElementById("menu-toggle");

        const controlPanel =
            document.getElementById("control-panel");

        const resetButton =
            document.getElementById("reset-map");


        // ========================================
        // 2. 대한민국 전체 지도 생성
        // ========================================

        const map = new kakao.maps.Map(mapElement, {
            center: new kakao.maps.LatLng(
                36.2,
                127.7
            ),
            level: 12
        });

        const infoWindow = new kakao.maps.InfoWindow({
            removable: true
        });

        // 대한민국 전체 표시 범위
        const koreaBounds = new kakao.maps.LatLngBounds(
            new kakao.maps.LatLng(33.0, 124.5),
            new kakao.maps.LatLng(38.7, 131.2)
        );

        // 대한민국 전체가 보이도록 설정
        map.setBounds(koreaBounds);

        // 더 이상 축소하지 못하도록 제한
        const nationwideLevel = map.getLevel();

        map.setMaxLevel(nationwideLevel);


        // ========================================
        // 3. 비행금지 / 비행제한 구역 로딩
        // ========================================

        try {
            await loadAirspaceZones(map);
        } catch (error) {
            console.error(
                "비행구역 데이터 로드 실패:",
                error
            );
        }


        // ========================================
        // 4. 햄버거 메뉴
        // ========================================

        if (menuToggle && controlPanel) {

            menuToggle.setAttribute(
                "aria-expanded",
                "true"
            );

            menuToggle.addEventListener(
                "click",
                function () {

                    const isHidden =
                        controlPanel.classList.toggle(
                            "is-hidden"
                        );

                    menuToggle.setAttribute(
                        "aria-expanded",
                        String(!isHidden)
                    );

                    menuToggle.setAttribute(
                        "aria-label",
                        isHidden
                            ? "제어 패널 열기"
                            : "제어 패널 닫기"
                    );
                }
            );
        }


        // ========================================
        // 5. 지역 JSON 데이터 불러오기
        // ========================================

        let regions = {};

        try {

            const response = await fetch(
                "/static/data/regions.json"
            );

            if (!response.ok) {
                throw new Error(
                    "지역 좌표 데이터를 불러오지 못했습니다."
                );
            }

            regions = await response.json();

        } catch (error) {

            console.error(
                "지역 데이터 오류:",
                error
            );

            if (statusElement) {
                statusElement.textContent =
                    "지역 데이터 로드 실패";
            }
        }


        // ========================================
        // 6. 시·도 목록 생성
        // ========================================

        function populateProvinces() {

            if (!provinceSelect || !citySelect) {
                return;
            }

            provinceSelect.innerHTML = "";

            // 전국 항목 추가
            const nationwideOption =
                document.createElement("option");

            nationwideOption.value = "전국";
            nationwideOption.textContent = "전국";

            provinceSelect.appendChild(
                nationwideOption
            );

            // regions.json에 있는 지역 추가
            Object.keys(regions).forEach(name => {

                const option =
                    document.createElement("option");

                option.value = name;
                option.textContent = name;

                provinceSelect.appendChild(option);
            });

            provinceSelect.value = "전국";

            populateCities("전국");
        }


        // ========================================
        // 7. 시·군·구 목록 생성
        // ========================================

        function populateCities(provinceName) {

            if (!citySelect) {
                return;
            }

            citySelect.innerHTML = "";

            // 전국 선택
            if (provinceName === "전국") {

                const option =
                    document.createElement("option");

                option.value = "전체";
                option.textContent = "전체";

                citySelect.appendChild(option);

                citySelect.disabled = true;

                return;
            }

            const region = regions[provinceName];

            if (!region) {
                citySelect.disabled = true;
                return;
            }

            citySelect.disabled = false;

            Object.keys(region.cities || {}).forEach(
                name => {

                    const option =
                        document.createElement("option");

                    option.value = name;
                    option.textContent = name;

                    citySelect.appendChild(option);
                }
            );

            citySelect.value = "전체";
        }


        // ========================================
        // 8. 전국 지도 복귀
        // ========================================

        function resetToNationwide() {

            // 전국 화면으로 이동
            map.setBounds(koreaBounds);

            // 지역 선택 초기화
            if (provinceSelect && citySelect) {

                provinceSelect.value = "전국";

                populateCities("전국");
            }

            // 기존 정보창 닫기
            infoWindow.close();
        }


        // ========================================
        // 9. 선택 지역으로 지도 이동
        // ========================================

        function moveToRegion() {

            if (!provinceSelect || !citySelect) {
                return;
            }

            const provinceName =
                provinceSelect.value;

            const cityName =
                citySelect.value;

            // 전국 선택 시 복귀
            if (provinceName === "전국") {

                resetToNationwide();

                return;
            }

            const region = regions[provinceName];

            if (!region) {
                return;
            }

            const coordinates =
                region.cities?.[cityName] ||
                region.center;

            if (!coordinates) {
                return;
            }

            const position = new kakao.maps.LatLng(
                coordinates[0],
                coordinates[1]
            );

            // 시·도 전체: 9
            // 시·군·구: 7
            const targetLevel =
                cityName === "전체" ? 9 : 7;

            // 지도 이동
            map.setLevel(targetLevel, {
                animate: false
            });

            map.setCenter(position);

            infoWindow.close();
        }


        // ========================================
        // 10. 지역 선택 이벤트
        // ========================================

        if (provinceSelect && citySelect) {

            populateProvinces();

            provinceSelect.addEventListener(
                "change",
                function () {

                    populateCities(
                        provinceSelect.value
                    );

                    moveToRegion();
                }
            );

            citySelect.addEventListener(
                "change",
                moveToRegion
            );
        }


        // ========================================
        // 11. 전국 지도 복귀 버튼
        // ========================================

        if (resetButton) {

            resetButton.addEventListener(
                "click",
                function () {

                    resetToNationwide();
                }
            );
        }


        // ========================================
        // 12. 기상 위험 데이터 관리
        // ========================================

        let riskZones = [];

        let loadTimer = null;

        let currentController = null;

        let requestId = 0;


        // ========================================
        // 13. 기상 위험 구역 조회
        // ========================================

        async function loadRiskZones() {

            const bounds = map.getBounds();

            const south =
                bounds.getSouthWest().getLat();

            const west =
                bounds.getSouthWest().getLng();

            const north =
                bounds.getNorthEast().getLat();

            const east =
                bounds.getNorthEast().getLng();

            const params = new URLSearchParams({
                south: south,
                west: west,
                north: north,
                east: east
            });

            // 이전 요청 취소
            if (currentController) {
                currentController.abort();
            }

            const controller =
                new AbortController();

            currentController = controller;

            const thisRequest = ++requestId;

            if (statusElement) {

                statusElement.textContent =
                    "기상 위험 구역 확인 중...";
            }

            try {

                const response = await fetch(
                    `/api/weather/zones?${params}`,
                    {
                        signal: controller.signal
                    }
                );

                const data = await response.json();

                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "기상 위험 구역 조회 실패"
                    );
                }

                // 이전 요청의 결과는 무시
                if (thisRequest !== requestId) {
                    return;
                }

                riskZones = data.zones || [];

                // 위험 데이터를 병합 격자에 적용
                drawRiskZones(
                    map,
                    riskZones,
                    infoWindow
                );

                if (statusElement) {

                    let message =
                        `위험 구역 ${riskZones.length}개 / ` +
                        `조회 격자 ${data.checked_grids}개`;

                    if (data.complete === false) {

                        message +=
                            " / 일부 지역 미조회";
                    }

                    if (data.failed_grids > 0) {

                        message +=
                            ` / 실패 ${data.failed_grids}개`;
                    }

                    statusElement.textContent = message;
                }

            } catch (error) {

                if (error.name === "AbortError") {
                    return;
                }

                if (thisRequest !== requestId) {
                    return;
                }

                console.error(
                    "기상 위험 구역 조회 오류:",
                    error
                );

                riskZones = [];

                drawRiskZones(
                    map,
                    riskZones,
                    infoWindow
                );

                if (statusElement) {

                    statusElement.textContent =
                        `조회 실패: ${error.message}`;
                }
            }
        }


        // ========================================
        // 14. 기상 API 호출 지연 처리
        // ========================================

        function scheduleLoad() {

            if (loadTimer) {
                clearTimeout(loadTimer);
            }

            loadTimer = setTimeout(
                loadRiskZones,
                500
            );
        }


        // ========================================
        // 15. 지도 이동 / 확대 / 축소 갱신
        // ========================================

        function updateMap() {

            // 기존 위험 데이터를 사용해
            // 병합 격자 먼저 표시
            drawMapGrids(
                map,
                riskZones,
                infoWindow
            );

            // 현재 지도 범위에 대한
            // 기상 위험 구역 재조회
            scheduleLoad();
        }


        // ========================================
        // 16. 지도 이벤트
        // ========================================

        kakao.maps.event.addListener(
            map,
            "idle",
            updateMap
        );


        // ========================================
        // 17. 최초 실행
        // ========================================

        updateMap();

    });
}
