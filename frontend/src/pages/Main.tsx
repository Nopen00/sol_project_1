
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  getAirspaceAnalysis,
  getWeather,
} from "../api/MainAnalysis";

import { searchKakaoLocation, suggestKakaoLocations } from "../features/map/kakaoSearch";
import type { SearchLocation } from "../types/kakao";
import "./Main.css";


/* ================================
   주요 기능 카드
================================ */

const FEATURES = [
  {
    to: "/map/restricted",
    icon: "🗺️",
    title: "드론 비행 지도",
    desc: "비행금지·제한 공역을 지도에서 확인해요.",
  },
  {
    to: "/map/weather",
    icon: "🌤️",
    title: "기상 분석",
    desc: "풍속·강수·기온 등 날씨를 조회해요.",
  },
  {
    to: "/map/suitability",
    icon: "📊",
    title: "비행 적합도",
    desc: "날씨와 기종으로 참고 점수를 받아요.",
  },
  {
    to: "/drone-info",
    icon: "🛸",
    title: "드론 정보",
    desc: "드론 기종별 소개와 사양을 살펴봐요.",
  },
];

/* ================================
   API 응답 타입
================================ */

type AirspaceResult = {
  status?: string;
  message?: string;
  airspace_count?: number;
};

type WeatherResult = {
  forecast_at?: string;
  temperature?: number;
  wind_speed?: number;
  precipitation?: number | string;
  precipitation_type?: string;
  precipitation_status?: string;
  precipitation_type_status?: string;
  precipitation_probability?: number;
  snowfall?: number | string;
};

/* ================================
   메인 페이지
================================ */

export default function Main() {
  const navigate = useNavigate();

  const [searchText, setSearchText] = useState("");
  const [selectedRegion, setSelectedRegion] = useState<SearchLocation | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SearchLocation | null>(null);
  const [suggestions, setSuggestions] = useState<SearchLocation[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [suggestionError, setSuggestionError] = useState("");

  /* 공역 및 날씨 결과 */
  const [airspace, setAirspace] =
    useState<AirspaceResult | null>(null);

  const [weather, setWeather] =
    useState<WeatherResult | null>(null);

  /* 오류 상태 */
  const [regionError, setRegionError] = useState("");
  const [airspaceError, setAirspaceError] = useState("");
  const [weatherError, setWeatherError] = useState("");

  /* 로딩 상태 */
  const [loading, setLoading] = useState(false);

  /* 중복 요청 결과 방지 */
  const requestIdRef = useRef(0);

  useEffect(() => {
    const keyword = searchText.trim();
    if (!showSuggestions || keyword.length < 2) return;

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setSuggestionLoading(true);
      setSuggestionError("");
      try {
        const result = await suggestKakaoLocations(keyword);
        if (!cancelled) setSuggestions(result);
      } catch (error) {
        if (!cancelled) {
          setSuggestions([]);
          setSuggestionError(error instanceof Error ? error.message : "추천 장소를 조회하지 못했습니다.");
        }
      } finally {
        if (!cancelled) setSuggestionLoading(false);
      }
    }, 350);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [searchText, showSuggestions]);

  /* ================================
     지역 검색 및 분석
  ================================ */

  async function handleSearch(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const keyword = searchText.trim();
    if (!keyword) {
      setRegionError("검색할 지역명 또는 주소를 입력해주세요.");
      return;
    }

    const currentRequestId = ++requestIdRef.current;
    setShowSuggestions(false);

    setRegionError("");
    setAirspaceError("");
    setWeatherError("");

    setSelectedRegion(null);
    setAirspace(null);
    setWeather(null);
    setLoading(true);

    let region: SearchLocation;
    try {
      region = selectedSuggestion && selectedSuggestion.name === keyword
        ? selectedSuggestion
        : await searchKakaoLocation(keyword);
    } catch (error) {
      if (currentRequestId !== requestIdRef.current) return;
      setRegionError(error instanceof Error ? error.message : "위치를 검색하지 못했습니다.");
      setLoading(false);
      return;
    }
    if (currentRequestId !== requestIdRef.current) return;
    setSelectedRegion(region);

    const [airspaceResult, weatherResult] =
      await Promise.allSettled([
        getAirspaceAnalysis(region.lat, region.lng),
        getWeather(region.lat, region.lng),
      ]);

    // 이전 검색 요청의 결과가 늦게 도착한 경우 무시
    if (currentRequestId !== requestIdRef.current) {
      return;
    }

    /* 공역 결과 */
    if (airspaceResult.status === "fulfilled") {
      setAirspace(airspaceResult.value);
    } else {
      console.error(
        "공역 조회 실패:",
        airspaceResult.reason
      );
      setAirspaceError(
        "비행 공역 정보를 조회하지 못했습니다."
      );
    }

    /* 날씨 결과 */
    if (weatherResult.status === "fulfilled") {
      setWeather(weatherResult.value);
    } else {
      console.error(
        "날씨 조회 실패:",
        weatherResult.reason
      );
      setWeatherError(
        "날씨 정보를 조회하지 못했습니다."
      );
    }

    setLoading(false);
  }

  /* ================================
     공역 카드 클릭 → 지도 페이지 이동
  ================================ */

  function handleAirspaceClick() {
    if (!selectedRegion) return;

    const params = new URLSearchParams({
      region: selectedRegion.name,
      lat: String(selectedRegion.lat),
      lng: String(selectedRegion.lng),
      level: String(selectedRegion.level ?? 6),
    });

    navigate(`/map/restricted?${params.toString()}`);
  }

  /* ================================
     화면 출력
  ================================ */

  return (
    <>
      {/* ===========================
          메인 상단 검색 영역
      =========================== */}

      <section className="main-hero">
        <h1>오늘, 드론 날려도 될까요?</h1>

        <p>
          비행 공역과 날씨를 한 번에 확인하고
          비행 계획을 세워 보세요.
        </p>

        <div className="main-search-wrapper">
          <form className="main-search" onSubmit={handleSearch}>
            <input
              type="search"
              aria-label="지역명 또는 주소 검색"
              aria-autocomplete="list"
              aria-expanded={showSuggestions && searchText.trim().length >= 2}
              aria-controls="main-search-suggestion-list"
              placeholder="지역명, 주소 또는 장소 입력 (예: 서울 강남구)"
              autoComplete="off"
              value={searchText}
              onChange={(event) => {
                setSearchText(event.target.value);
                setSelectedSuggestion(null);
                setSuggestions([]);
                setShowSuggestions(true);
                setSuggestionLoading(false);
                setSuggestionError("");
                setRegionError("");
              }}
              onFocus={() => setShowSuggestions(true)}
              onKeyDown={(event) => {
                if (event.key === "Escape") setShowSuggestions(false);
              }}
            />
            <button type="submit" disabled={loading}>
              {loading ? "조회 중..." : "검색"}
            </button>
          </form>

          {showSuggestions && searchText.trim().length >= 2 && (
            <div id="main-search-suggestion-list" className="search-autocomplete" role="listbox" aria-label="장소 검색 결과">
              {suggestionLoading ? (
                <div className="search-autocomplete-message">검색 중...</div>
              ) : suggestionError ? (
                <div className="search-autocomplete-message" role="status">{suggestionError}</div>
              ) : suggestions.length === 0 ? (
                <div className="search-autocomplete-message">추천 장소가 없습니다. 검색 버튼으로 주소 검색을 시도할 수 있습니다.</div>
              ) : (
                suggestions.map((place, index) => (
                  <button
                    key={`${place.lat}-${place.lng}-${index}`}
                    type="button"
                    role="option"
                    aria-selected={false}
                    className="search-autocomplete-item"
                    onClick={() => {
                      setSearchText(place.name);
                      setSelectedSuggestion(place);
                      setShowSuggestions(false);
                      setSuggestions([]);
                    }}
                  >
                    📍 {place.name}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {regionError && (
          <p role="alert">{regionError}</p>
        )}
      </section>

      {/* ===========================
          지역 분석 결과
      =========================== */}

      {selectedRegion && (
        <section className="main-results">
          <h2>지역 분석 결과</h2>

          <p className="main-results__location">
            📍 {selectedRegion.name}
          </p>

          <div className="main-results__grid">

            {/* =====================
                비행 공역 정보
            ===================== */}

           <article className="main-result-card">
                <h3>🗺️ 비행 공역 정보</h3>

                {loading && <p>공역 정보를 조회 중입니다...</p>}

                {airspaceError && (
                  <p role="alert">{airspaceError}</p>
                )}

                {airspace && (
                  <>
                    <p>
                      <strong>공역 상태:</strong>{" "}
                      {airspace.status ?? "확인 필요"}
                    </p>

                    <p>
                      <strong>조회된 공역 수:</strong>{" "}
                      {airspace.airspace_count ?? 0}
                    </p>

                    <p>{airspace.message}</p>
                  </>
                )}

                {/* 글씨를 클릭할 때만 지도 페이지 이동 */}
                <button
                  type="button"
                  className="main-result-card__link"
                  onClick={handleAirspaceClick}
                >
                  지도에서 자세히 보기 →
                </button>
            </article>
            {/* =====================
                날씨 정보
            ===================== */}

            <article className="main-result-card">
              <h3>🌤️ 날씨 정보</h3>

              {loading && (
                <p>날씨 정보를 조회 중입니다...</p>
              )}

              {weatherError && (
                <p role="alert">{weatherError}</p>
              )}

              {weather && (
                <>
                  <p>
                    <strong>예보 시간:</strong>{" "}
                    {weather.forecast_at ?? "-"}
                  </p>

                  <p>
                    <strong>기온:</strong>{" "}
                    {weather.temperature ?? "-"}°C
                  </p>

                  <p>
                    <strong>풍속:</strong>{" "}
                    {weather.wind_speed ?? "-"} m/s
                  </p>

                  <p>
                    <strong>강수량:</strong>{" "}
                    {weather.precipitation ?? "-"}
                  </p>

                  <p>
                    <strong>강수 형태:</strong>{" "}
                    {weather.precipitation_type ?? "-"}
                  </p>

                  {weather.precipitation_probability !==
                    undefined && (
                    <p>
                      <strong>강수 확률:</strong>{" "}
                      {weather.precipitation_probability}%
                    </p>
                  )}

                  {weather.snowfall !== undefined && (
                    <p>
                      <strong>적설량:</strong>{" "}
                      {weather.snowfall}
                    </p>
                  )}
                </>
              )}
            </article>
          </div>

          <p className="main-results__notice">
            검색한 위치의 좌표를 기준으로 조회한 참고 정보입니다.
            지역 전체의 상태를 의미하지 않으며, 실제 비행 승인은 최신 공식 정보로 확인하세요.
          </p>
        </section>
      )}

      {/* ===========================
          주요 기능 카드
      =========================== */}

      <section className="main-features">
        <h2>주요 기능</h2>

        <ul className="main-features__list">
          {FEATURES.map((feature) => (
            <li key={feature.to}>
              <Link
                to={feature.to}
                className="main-card"
              >
                <span className="main-card__icon">
                  {feature.icon}
                </span>

                <strong>
                  {feature.title}
                </strong>

                <span>
                  {feature.desc}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
