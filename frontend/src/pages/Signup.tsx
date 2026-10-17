import { type FormEvent, useState } from "react";

export default function Signup() {
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [agree, setAgree] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (password !== passwordConfirm) {
      setMessage("비밀번호를 다시 확인해주세요.");

      return;
    }
    if (!agree) {
      setMessage("약관동의가 필요합니다.");

      return;
    }
    setMessage("확인되었습니다.");
  };

  return (
    <section>
      <h1>회원가입</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="nickname">닉네임 : </label>
          <input
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            type="text"
            id="nickname"
          />
        </div>
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
          <label htmlFor="passwordConfirm">비밀번호 확인 : </label>
          <input
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            type="password"
            id="passwordConfirm"
          />
        </div>

        <div>
          <input
            type="checkbox"
            id="agree"
            checked={agree}
            onChange={(e) => setAgree(e.target.checked)}
          />
          <label htmlFor="agree"> 개인정보 이용약관에 동의합니다</label>
        </div>

        <button type="submit">가입하기</button>
        <p>{message}</p>
      </form>

      <h2>아직 개발중인 기능입니다.</h2>
    </section>
  );
}
