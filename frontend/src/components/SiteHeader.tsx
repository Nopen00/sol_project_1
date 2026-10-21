import { Link } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "메인" },
  { to: "/map/restricted", label: "비행제한 지도" },
  { to: "/map/weather", label: "날씨 지도" },
  { to: "/map/suitability", label: "적합도 지도" },
  { to: "/drone-info", label: "드론 정보" },
];

export default function SiteHeader() {
  return (
    <header>
      <nav>
        <ul>
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <Link to={item.to}>{item.label}</Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
