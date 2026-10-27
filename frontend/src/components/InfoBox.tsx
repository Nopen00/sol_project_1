import type { ReactNode } from "react";
import "./InfoBox.css";

interface InfoBoxProps {
  title: string;
  children: ReactNode;
}

export default function InfoBox({ title, children }: InfoBoxProps) {
  return (
    <div className="info-box">
      <h3 className="info-box__title">{title}</h3>
      <div className="info-box__body">{children}</div>
    </div>
  );
}
