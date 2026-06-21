import type { MetricsResponse } from "../types/api";

type Props = {
  metrics: MetricsResponse | null;
  loading: boolean;
  onRefresh: () => void;
};

export function KpiCards({ metrics, loading, onRefresh }: Props) {
  return (
    <section className="section kpi-section" aria-labelledby="kpi-heading">
      <div className="section-head">
        <h2 id="kpi-heading">Indicadores</h2>
        <button type="button" className="btn btn-secondary" onClick={onRefresh} disabled={loading}>
          {loading ? "Actualizando…" : "Actualizar datos"}
        </button>
      </div>
      <div className="kpi-grid">
        <article className="kpi-card">
          <span className="kpi-label">Total tickets</span>
          <strong className="kpi-value">{metrics?.total_tickets ?? "—"}</strong>
        </article>
        <article className="kpi-card">
          <span className="kpi-label">Con análisis IA</span>
          <strong className="kpi-value">{metrics?.analyzed_tickets ?? "—"}</strong>
        </article>
        <article className="kpi-card">
          <span className="kpi-label">Pendientes de IA</span>
          <strong className="kpi-value">{metrics?.pending_analysis ?? "—"}</strong>
        </article>
        <article className="kpi-card kpi-accent">
          <span className="kpi-label">Alta / crítica</span>
          <strong className="kpi-value">{metrics?.high_or_critical ?? "—"}</strong>
        </article>
        <article className="kpi-card">
          <span className="kpi-label">Compras últimos 7 días</span>
          <strong className="kpi-value">{metrics?.tickets_last_7_days ?? "—"}</strong>
        </article>
      </div>
    </section>
  );
}
