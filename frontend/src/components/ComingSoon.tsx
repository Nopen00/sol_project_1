import { Link } from 'react-router-dom';

// 아직 만들지 않은 페이지 주소로 들어왔을 때 보여주는 임시 화면
export default function ComingSoon() {
  return (
    <section style={{ padding: 'var(--space-12) var(--space-4)', textAlign: 'center' }}>
      <h1>준비 중인 페이지예요</h1>
      <p>곧 만나볼 수 있어요.</p>
      <Link to="/">메인으로 돌아가기</Link>
    </section>
  );
}
