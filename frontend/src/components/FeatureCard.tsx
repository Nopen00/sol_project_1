import { Link } from "react-router-dom";

interface FeatureCardProps {
  to: string;
  title: string;
  description: string;
}

export default function FeatureCard({
  to,
  title,
  description,
}: FeatureCardProps) {
  return (
    <Link to={to}>
      <h3>{title}</h3>
      <p>{description}</p>
    </Link>
  );
}
