import type { DroneModel } from "../../types/drone";

interface DroneSelectProps {
  options: DroneModel[];
  value: string;
  onChange: (id: string) => void;
}

export default function DroneSelect({
  options,
  value,
  onChange,
}: DroneSelectProps) {
  return (
    <div className="drone-select">
      <label htmlFor="drone-select">드론 기종 </label>
      <select
        id="drone-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">--기종을 선택하세요--</option>
        {options.map((drone) => (
          <option key={drone.id} value={drone.id}>
            {drone.name}
          </option>
        ))}
      </select>
    </div>
  );
}
