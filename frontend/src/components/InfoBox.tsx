import type { ReactNode } from "react";

interface InfoBoxProps {
  title: string;
  children: ReactNode;
}

export default function InfoBox({ title, children }: InfoBoxProps) {
  return (
    <div>
      <h3>{title}</h3>
      <div>{children}</div>
    </div>
  );
}
