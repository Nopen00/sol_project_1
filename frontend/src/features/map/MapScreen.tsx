interface MapScreenProps {
  mode: string;
}

export const MapScreen = ({ mode }: MapScreenProps) => {
  return (
    <section>
      <h2>{mode} 지도</h2>
      <div style={{ height: "70vh" }}>지도가 들어갈 자리</div>
    </section>
  );
};
