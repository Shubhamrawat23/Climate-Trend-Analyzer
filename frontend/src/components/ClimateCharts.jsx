import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function ClimateCharts({ data }) {
  const annualMetrics = data ?? [];
  // console.log(data);
  

  if (annualMetrics.length === 0) {
    return <p>No annual climate data available to display.</p>;
  }

  const chartData = annualMetrics.map((item) => ({
    year: String(item.year),
    events: item.event_count,
    heatwaveDays: item.total_heatwave_days,
  }));

  return (
    <section>
      <div className="text-2xl font-semibold">Heatwave Trends</div>
      <br/>
      <div className="chart-container">
        <div className="text-sm">Annual Heatwave Frequency</div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis
              allowDecimals={false}
              label={{
                value: "Events",
                angle: -90,
                position: "insideLeft",
              }}
            />
            <Tooltip />
            <Legend />

            <Line
              type="monotone"
              dataKey="events"
              name="Heatwave events"
              stroke="#e76f51"
              strokeWidth={2}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-container">
        <div className="text-sm">Annual Heatwave Days</div>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis
              allowDecimals={false}
              label={{
                value: "Days",
                angle: -90,
                position: "insideLeft",
              }}
            />
            <Tooltip />
            <Legend />

            <Bar
              dataKey="heatwaveDays"
              name="Heatwave days"
              fill="#f4a261"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}