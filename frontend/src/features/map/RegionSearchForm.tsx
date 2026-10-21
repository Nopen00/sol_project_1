import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function RegionSearchForm() {
  const [keyword, setKeyword] = useState("");
  const navigate = useNavigate();

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = keyword.trim();

    if (!trimmed) return;
    navigate(`/map/restricted?q=${encodeURIComponent(trimmed)}`);
  };

  return (
    <form onSubmit={handleSearchSubmit}>
      <label htmlFor="region-search">지역 검색 </label>
      <input
        type="text"
        id="region-search"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
      />
      <button type="submit">검색</button>
    </form>
  );
}
