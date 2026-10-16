import { Outlet } from 'react-router-dom';
import Header from './Header';
import './Layout.css';

export default function Layout() {
  return (
    <>
      <Header />
      <main className="layout__main">
        <Outlet />
      </main>
      <footer className="layout__footer">
        <p>
          비행 적합도는 참고용입니다. 실제 비행 승인은 최신 공식 정보(드론원스톱 등)로
          확인해 주세요.
        </p>
      </footer>
    </>
  );
}
