import FeatureCard from "../components/FeatureCard";
import RegionSearchForm from "../features/map/RegionSearchForm";

const FEATURE_CARDS = [
  {
    to: "/map/restricted",
    title: "비행 제한 지도🚫",
    description: "비행금지·제한 공역을 지도에서 확인하세요",
  },
  {
    to: "/map/weather",
    title: "날씨 지도☀️",
    description: "풍속·강수·기온을 확인하세요",
  },
  {
    to: "/map/suitability",
    title: "비행 적합도 지도📊",
    description: "드론 비행을 해도 될 지 적합도를 확인하세요",
  },
  {
    to: "/drone-info",
    title: "드론 정보🛸",
    description: "드론 기종 정보를 확인하세요",
  },
];

export default function MainPage() {
  return (
    <section>
      <h1>드론 비행 안내</h1>
      <p>비행 공역과 날씨를 한 번에 확인하고 비행 계획을 세워 보세요.</p>
      <RegionSearchForm />
      <ul>
        {FEATURE_CARDS.map((card) => (
          <li key={card.to}>
            <FeatureCard
              to={card.to}
              title={card.title}
              description={card.description}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
