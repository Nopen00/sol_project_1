import { useState, type FormEvent } from "react";
import { useAuth } from "../features/auth/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const { login } = useAuth();
  const navigate = useNavigate();
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    login();
    navigate("/");
  };

  return (
    <section>
      <h1>로그인</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">이메일 : </label>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            id="email"
          />
        </div>
        <div>
          <label htmlFor="password">비밀번호 : </label>
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            id="password"
          />
        </div>
        <div>
          <button type="submit">로그인</button>
        </div>
      </form>
      <h2>아직 개발중인 기능입니다.</h2>
    </section>
  );
}
