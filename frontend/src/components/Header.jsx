const HAZARDS = [
  { value: "heatwave", label: "Heatwave", disabled: false },
  { value: "drought", label: "Drought (soon)", disabled: true },
  { value: "rain", label: "Heavy rainfall (soon)", disabled: true },
];

export default function Header({ hazard, onHazardChange }) {
  return (
    <header className="rounded-xl border border-slate-500 px-4 py-3 shadow-sm sm:px-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-semibold sm:text-lg">
            Climate Hazard Trend Analyzer
          </h1>
        </div>

        <div className="flex items-center justify-between gap-3 sm:justify-end">
          <select
            value={hazard}
            onChange={(e) => onHazardChange(e.target.value)}
            className="rounded-md border border-slate-500 px-3 py-1.5 text-sm"
          >
            {HAZARDS.map((h) => (
              <option key={h.value} value={h.value} disabled={h.disabled}>
                {h.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}
