import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MetricsResponse } from "../types/api";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b", "#0ea5e9", "#d946ef"];

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#16a34a",
  neutral: "#64748b",
  negative: "#dc2626",
};

type Props = {
  metrics: MetricsResponse | null;
};

export function ChartsPanel({ metrics }: Props) {
  if (!metrics) {
    return (
      <section className="section charts-section muted" aria-label="Gráficos">
        Sin métricas aún. Comprueba que el API responda en <code>/metrics</code>.
      </section>
    );
  }

  const priorityData = Object.entries(metrics.by_priority)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const categoryData = Object.entries(metrics.by_category)
    .map(([name, value]) => ({
      name: name.length > 18 ? `${name.slice(0, 18)}…` : name,
      fullName: name,
      value,
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  const sentimentData = Object.entries(metrics.by_sentiment).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <section className="section charts-section" aria-labelledby="charts-heading">
      <h2 id="charts-heading">Visualizaciones</h2>
      <div className="charts-grid">
        <figure className="chart-card">
          <figcaption>Tickets por prioridad (efectiva)</figcaption>
          <div className="chart-box">
            {priorityData.length === 0 ? (
              <p className="muted chart-empty">Sin datos de prioridad.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={priorityData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v: number) => [v, "Tickets"]} />
                  <Bar dataKey="value" name="Tickets" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </figure>

        <figure className="chart-card">
          <figcaption>Top categorías (frecuencia)</figcaption>
          <div className="chart-box chart-box--tall">
            {categoryData.length === 0 ? (
              <p className="muted chart-empty">Sin categorías agregadas.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={categoryData} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" name="Tickets" radius={[0, 4, 4, 0]}>
                    {categoryData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </figure>

        <figure className="chart-card">
          <figcaption>Sentimiento (IA)</figcaption>
          <div className="chart-box">
            {sentimentData.length === 0 ? (
              <p className="muted chart-empty">Aún no hay tickets analizados con sentimiento.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={88}
                    label={false}
                  >
                    {sentimentData.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={SENTIMENT_COLORS[entry.name.toLowerCase()] ?? COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </figure>
      </div>
    </section>
  );
}
