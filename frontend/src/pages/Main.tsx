import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Main.css";

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

export default function Main() {
  const [keyword, setKeyword] = useState("");
  const navigate = useNavigate();

  // 검색어를 들고 지 도 페이지로 이동한다. 실제 검색은 지도 기능(features/map)에서 처리한다.
  const handleSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = keyword.trim();
    if (!trimmed) return;
    navigate(`/map?q=${encodeURIComponent(trimmed)}`);
  };

  return (
    <>
      <section className="main-hero">
        <h1>오늘, 드론 날려도 될까요?</h1>
        <p>비행 공역과 날씨를 한 번에 확인하고 비행 계획을 세워 보세요.</p>

        <form className="main-search" onSubmit={handleSearch}>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="지역이나 주소를 입력하세요"
            aria-label="지역 검색"
          />
          <button type="submit">검색</button>
        </form>
      </section>

      <section className="main-features">
        {/* <h2></h2> */}
        <ul className="main-features__list">
          {FEATURES.map((f) => (
            <li key={f.to}>
              <Link to={f.to} className="main-card">
                <span className="main-card__icon">{f.icon}</span>
                <strong>{f.title}</strong>
                <span>{f.desc}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
