import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
// import { useAuth } from "../features/auth/AuthContext";
import "./Header.css";

const MENUS = [
  { to: "/map/restricted", label: "드론 비행 지도" },
  { to: "/map/weather", label: "기상 분석" },
  { to: "/map/suitability", label: "비행 적합도" },
  { to: "/drone-info", label: "드론 정보" },
  { to: "/news", label: "최신 정보·영상" },
];

export default function Header() {
  // const { isLoggedIn, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const closeMenu = () => setIsOpen(false);

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="header__logo" onClick={closeMenu}>
          🛸 드론 비행 안내
        </Link>

        <button
          type="button"
          className="header__toggle"
          aria-label="메뉴 열기"
          aria-expanded={isOpen}
          onClick={() => setIsOpen((prev) => !prev)}
        >
          ☰
        </button>

        <nav className={`header__nav ${isOpen ? "header__nav--open" : ""}`}>
          <ul className="header__menu">
            {MENUS.map((menu) => (
              <li key={menu.to}>
                <NavLink to={menu.to} onClick={closeMenu}>
                  {menu.label}
                </NavLink>
              </li>
            ))}
          </ul>

          {/* <div className="header__auth">
            {isLoggedIn ? (
              <>
                <Link to="/mypage" onClick={closeMenu}>
                  마이페이지
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    closeMenu();
                  }}
                >
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <Link to="/login" onClick={closeMenu}>
                  로그인
                </Link>
                <Link
                  to="/signup"
                  className="header__signup"
                  onClick={closeMenu}
                >
                  회원가입
                </Link>
              </>
            )}
          </div> */}
        </nav>
      </div>
    </header>
  );
}
