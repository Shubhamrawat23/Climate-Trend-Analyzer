import { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import MapPicker from "./MapPicker";

export default function FilterPanel({ initial, onAnalyze, onReset, status }) {
  const [draft, setDraft] = useState(initial);
  const [error, setError] = useState("");
  const set = (patch) => {
    setError("");
    console.log(draft);
    
    setDraft((d) => ({ ...d, ...patch }));
  };

  // Latest selectable day = end of today
  const today = new Date();
  today.setHours(23, 59, 59, 999);

  const submit = () => {
    const regionOk =
      (draft.regionType === "city" && draft.city.trim()) ||
      (draft.regionType === "latlon" && draft.lat !== "" && draft.lon !== "") ||
      (draft.regionType === "map" && draft.pin !== null);

    if (!regionOk) return setError("Choose a region first.");
    if (!draft.from || !draft.to) return setError("Pick both From and To dates.");
    if (draft.from > draft.to) return setError("From date must be before To date.");
    onAnalyze(draft);
  };

  const inputClass =
    "w-full rounded-md border border-slate-500 bg-transparent px-3 py-2 text-sm " +
    "outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100 cursor-pointer";

  return (
    <aside className="rounded-xl border border-slate-500 p-4 shadow-sm sm:p-5">
      <div className="space-y-4">
        {/* Region */}
        <div>
          <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide">
            Region
          </label>
          <select
            value={draft.regionType}
            onChange={(e) => set({ regionType: e.target.value })}
            className="w-full rounded-md border border-slate-500 px-3 py-2 text-sm outline-none [color-scheme:dark] focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
          >
            <option value="" disabled>Select region type</option>
            <option value="city" className="bg-black text-white">City / State</option>
            <option value="latlon">Custom lat-lon</option>
            <option value="map">Map</option>
          </select>
        </div>

        {draft.regionType === "city" && (
          <input
            type="text"
            value={draft.city}
            placeholder="Enter city or state"
            onChange={(e) => set({ city: e.target.value })}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
          />
        )}

        {draft.regionType === "latlon" && (
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              step="0.01"
              placeholder="Latitude"
              value={draft.lat}
              onChange={(e) => set({ lat: e.target.value })}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
            <input
              type="number"
              step="0.01"
              placeholder="Longitude"
              value={draft.lon}
              onChange={(e) => set({ lon: e.target.value })}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
          </div>
        )}

        {draft.regionType === "map" && (
          <div className="space-y-2" >
            <p className="text-sm text-gray-600">
              Click anywhere on the map to select a location.
            </p>

            <MapPicker
              position={draft.pin}
              onSelect={([lat, lon]) =>
                set({
                  pin: [lat, lon],
                  lat: String(lat),
                  lon: String(lon),
                })
              }
            />

            {draft.pin && (
              <p className="text-sm">
                Selected coordinates:{" "}
                {draft.pin[0].toFixed(4)}, {draft.pin[1].toFixed(4)}
              </p>
            )}
          </div>
        )}

        {/* Dates */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
          <div>
            <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide">
              From
            </label>
            <DatePicker
              selected={draft.from || null}
              onChange={(date) => set({ from: date.toISOString().slice(0, 10) })}
              maxDate={today}
              dateFormat="yyyy-MM-dd"
              placeholderText="Select start date"
              className={inputClass}
              wrapperClassName="w-full"
              calendarClassName="tw-datepicker"
              popperClassName="tw-datepicker-popper"
              showPopperArrow={false}
              popperPlacement="bottom-start"
              showMonthDropdown
              showYearDropdown
              dropdownMode="select"
              showOutsideDays={false}
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide">
              To
            </label>
            <DatePicker
              selected={draft.to || null}
              onChange={(date) => set({ to: date.toISOString().slice(0, 10) })}
              minDate={draft.from || undefined}
              maxDate={today}
              dateFormat="yyyy-MM-dd"
              placeholderText="Select end date"
              className={inputClass}
              wrapperClassName="w-full"
              calendarClassName="tw-datepicker"
              popperClassName="tw-datepicker-popper"
              showPopperArrow={false}
              popperPlacement="bottom-start"
              showMonthDropdown
              showYearDropdown
              dropdownMode="select"
              showOutsideDays={false}
            />
          </div>
        </div>

        {error && <p className="text-xs text-red-600">{error}</p>}

        <div className="flex gap-2">
          <button
            onClick={() => { setError(""); setDraft(onReset()); }}
            className="flex-1 rounded-md border border-slate-300 py-2 text-sm font-medium hover:bg-slate-50 hover:text-slate-800 cursor-pointer"
          >
            Reset
          </button>
          <button
            onClick={submit}
            className="flex-1 rounded-md bg-orange-500 py-2 text-sm font-semibold text-white transition hover:bg-orange-600 cursor-pointer"
          >
            {status == "loading" ? "Analyzing…" : "Analyze"}
          </button>
        </div>
      </div>
    </aside>
  );
}