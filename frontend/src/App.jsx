import { useCallback, useRef, useState, useEffect } from "react";
import Header from "./components/Header";
import FilterPanel from "./components/FilterPanel";
import ClimateCharts from "./components/ClimateCharts";
import KeyInsights from "./components/KeyInsights";

const API_URL = `${import.meta.env.VITE_API_URL || ""}/api/analysis`;

export const EMPTY_FILTERS = {
  regionType: "",
  city: "",
  lat: "",
  lon: "",
  pin: null,
  from: "",
  to: "",
};

export default function App() {
  const [hazard, setHazard] = useState("heatwave");
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const apiRef = useRef();
  const reportRef = useRef(null);

  useEffect(() => () => apiRef.current?.abort(), []);

  const handleAnalyze = useCallback(async (filters) => {
    apiRef.current?.abort();
    const controller = new AbortController();
    apiRef.current = controller;

    setStatus("loading");

    try {
      const byName = filters.regionType === "city";
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", accept: "application/json" },
        body: JSON.stringify({
          region: byName ? filters.city.trim() : null,
          lat: byName ? null : Number(filters.lat),
          lon: byName ? null : Number(filters.lon),
          start_date: filters.from,
          end_date: filters.to,
        }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(await readErrorMessage(res));

      let data;
      try {
        data = await res.json();
      } catch (e) {
        if (e.name === "AbortError") throw e;
        throw new Error("The server sent back an invalid response.");
      }

      if (!Array.isArray(data?.annual_metrics) || !data?.insights) {
        throw new Error("The server sent back data in an unexpected format.");
      }

      if (apiRef.current !== controller) return;

      setResult(data);
      setStatus("success");
    } catch (err) {
      if (apiRef.current !== controller) return;

      let message;
      if (err instanceof TypeError) {
        message = "Can't reach the server. Check that the API is running and try again.";
      } else {
        message = err.message || "Something went wrong. Try again.";
      }

      setResult(null);
      setStatus("error");
      alert(message); // Immediate alert for API/network errors
    }
  }, []);

  async function readErrorMessage(res) {
    let text = "";
    let body = null;
    try {
      text = await res.text();
      body = JSON.parse(text);
    } catch { }
    const detail = body?.detail;

    if (res.status >= 500 && !text.trim()) return "Can't reach the server. Check that the API is running and try again.";
    if ((res.status === 503 || res.status === 504) && !detail) return "The server is busy or not responding. Try again in a moment.";
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length) {
      return detail
        .map((d) => {
          const msg = String(d.msg || "Invalid value").replace(/^Value error,\s*/, "");
          const field = Array.isArray(d.loc) ? d.loc.filter((p) => p !== "body").join(".") : "";
          return field ? `${field}: ${msg}` : msg;
        })
        .join(" ");
    }

    if (res.status === 404) return "The analysis service was not found. Check the API address.";
    if (res.status === 429) return "Too many requests. Wait a moment and try again.";
    if (res.status >= 500) return "The server ran into a problem. Try again in a moment.";
    return `Request failed (${res.status}).`;
  }

  const handleReset = () => {
    setResult(null);
    setStatus("idle");
    return EMPTY_FILTERS;
  };

  const handleExportCSV = () => {
    if (!result?.annual_metrics) return;

    const csvRows = [];


    csvRows.push(["CLIMATE HAZARD TREND REPORT"]);
    csvRows.push([`Generated On: ${new Date().toISOString()}`]);
    csvRows.push([]);

    csvRows.push(["--- Annual Metrics ---"]);
    csvRows.push(["Year", "Heatwave Events", "Total Heatwave Days"]);

    result.annual_metrics.forEach((item) => {
      csvRows.push([
        item.year,
        item.event_count,
        item.total_heatwave_days
      ]);
    });

    csvRows.push([]);
    csvRows.push([]); 

    csvRows.push(["--- Key Insights & Analysis ---"]);
    csvRows.push(["Metric / Category", "Detailed Observation "]);

    if (result.insights) {
      Object.entries(result.insights).forEach(([key, text]) => {
        const formattedTitle = key
          .replace(/[_]/g, " ")
          .replace(/\b\w/g, (char) => char.toUpperCase());

        const sanitizedText = `"${text.replace(/"/g, '""')}"`;

        csvRows.push([formattedTitle, sanitizedText]);
      });
    }

    // Generate and trigger download
    const csvContent = csvRows.map((row) => row.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `climate_hazard_report_${hazard}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-4 px-3 py-4 sm:space-y-5 sm:px-5 sm:py-6">
        <Header hazard={hazard} onHazardChange={setHazard} />

        <div className="grid gap-4 sm:gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
          <FilterPanel initial={EMPTY_FILTERS} onAnalyze={handleAnalyze} onReset={handleReset} status={status} />

          <div className="min-w-0 space-y-4 sm:space-y-5">
            {status === "loading" && (
              <div className="flex h-[350px] w-full flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/50 p-6 text-center shadow-inner">
                <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-slate-500 border-t-slate-100" />
                <p className="text-sm font-medium text-slate-300">Analyzing climate hazard trend data...</p>
                <p className="mt-1 text-xs text-slate-500">Computing historical trends and slope metrics</p>
              </div>
            )}

            {status === "idle" && (
              <div className="flex h-[350px] w-full flex-col items-center justify-center rounded-lg border border-dashed border-slate-800 bg-slate-900/20 p-6 text-center">
                <p className="text-sm text-slate-400">Select a region and date range on the left, then click <span className="font-semibold text-slate-200">Analyze</span> to view trends.</p>
              </div>
            )}

            {status === "success" && result && (
              <div ref={reportRef} id="climate-report">
                <ClimateCharts data={result?.annual_metrics} />
                <KeyInsights insights={result?.insights} />
              </div>
            )}
          </div>
        </div>

        {status === "success" && result && (
          <div className="print:hidden pt-2">
            <button
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium cursor-pointer shadow-sm hover:border-slate-500 hover:bg-slate-800 sm:w-auto"
              onClick={handleExportCSV}
            >
              Export CSV
            </button>
          </div>
        )}
      </div>
    </div>
  );
}