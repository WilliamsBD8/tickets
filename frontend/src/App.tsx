import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchMetrics } from "./api/metrics";
import { fetchTickets, triggerAnalyze } from "./api/tickets";
import { AskPanel } from "./components/AskPanel";
import { ChartsPanel } from "./components/ChartsPanel";
import { FiltersBar } from "./components/FiltersBar";
import { KpiCards } from "./components/KpiCards";
import { TicketsTable } from "./components/TicketsTable";
import type { MetricsResponse, TicketEnriched, TicketListQuery } from "./types/api";

const DEFAULT_QUERY: TicketListQuery = {
  page: 1,
  page_size: 25,
};

function errMsg(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

export default function App() {
  const [applied, setApplied] = useState<TicketListQuery>(DEFAULT_QUERY);
  const [draft, setDraft] = useState<TicketListQuery>(DEFAULT_QUERY);

  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(true);

  const [tickets, setTickets] = useState<TicketEnriched[]>([]);
  const [total, setTotal] = useState(0);
  const [ticketsLoading, setTicketsLoading] = useState(true);

  const [globalError, setGlobalError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const refreshMetrics = useCallback(async () => {
    setMetricsLoading(true);
    setGlobalError(null);
    try {
      const m = await fetchMetrics();
      setMetrics(m);
    } catch (e) {
      setGlobalError(errMsg(e));
    } finally {
      setMetricsLoading(false);
    }
  }, []);

  const loadTickets = useCallback(async () => {
    setTicketsLoading(true);
    setGlobalError(null);
    try {
      let query: TicketListQuery = { ...applied };
      let t = await fetchTickets(query);
      const ps = query.page_size ?? 25;
      const tp = Math.max(1, Math.ceil(t.total / ps));
      const currentPage = query.page ?? 1;
      if (currentPage > tp) {
        query = { ...query, page: tp };
        setApplied(query);
        setDraft((d) => ({ ...d, page: tp }));
        t = await fetchTickets(query);
      }
      setTickets(t.items);
      setTotal(t.total);
    } catch (e) {
      setGlobalError(errMsg(e));
    } finally {
      setTicketsLoading(false);
    }
  }, [applied]);

  useEffect(() => {
    void refreshMetrics();
  }, [refreshMetrics]);

  useEffect(() => {
    void loadTickets();
  }, [loadTickets]);

  const totalPages = useMemo(() => {
    const ps = applied.page_size ?? 25;
    return Math.max(1, Math.ceil(total / ps));
  }, [total, applied.page_size]);

  const onApply = () => setApplied({ ...draft, page: 1 });

  const onReset = () => {
    setDraft({ ...DEFAULT_QUERY });
    setApplied({ ...DEFAULT_QUERY });
  };

  const onAnalyze = async () => {
    setAnalyzing(true);
    setGlobalError(null);
    try {
      await triggerAnalyze(800);
      await refreshMetrics();
      await loadTickets();
    } catch (e) {
      setGlobalError(errMsg(e));
    } finally {
      setAnalyzing(false);
    }
  };

  const goPage = (p: number) => {
    const next = Math.min(Math.max(1, p), totalPages);
    setApplied((prev) => ({ ...prev, page: next }));
    setDraft((d) => ({ ...d, page: next }));
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>AI Support Ticket Analyzer</h1>
          <p className="muted">Dashboard: tickets enriquecidos por IA, KPIs y consultas en lenguaje natural.</p>
        </div>
      </header>

      {globalError ? (
        <div className="error-banner" role="alert">
          {globalError}
        </div>
      ) : null}

      <KpiCards metrics={metrics} loading={metricsLoading} onRefresh={refreshMetrics} />

      <ChartsPanel metrics={metrics} />

      <FiltersBar
        draft={draft}
        onChange={setDraft}
        onApply={onApply}
        onReset={onReset}
        analyzing={analyzing}
        onAnalyze={onAnalyze}
      />

      <section className="section table-section" aria-labelledby="table-heading">
        <div className="section-head">
          <h2 id="table-heading">Tickets</h2>
          <div className="pagination">
            <label className="field inline">
              <span className="sr-only">Tamaño de página</span>
              <select
                value={applied.page_size ?? 25}
                onChange={(e) => {
                  const page_size = Number(e.target.value);
                  setApplied((p) => ({ ...p, page: 1, page_size }));
                  setDraft((d) => ({ ...d, page_size }));
                }}
              >
                {[25, 50, 100].map((n) => (
                  <option key={n} value={n}>
                    {n} / página
                  </option>
                ))}
              </select>
            </label>
            <span className="muted small">
              Página {applied.page ?? 1} de {totalPages} — {total} resultados
            </span>
            <button type="button" className="btn btn-secondary" onClick={() => goPage((applied.page ?? 1) - 1)} disabled={(applied.page ?? 1) <= 1}>
              Anterior
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => goPage((applied.page ?? 1) + 1)}
              disabled={(applied.page ?? 1) >= totalPages}
            >
              Siguiente
            </button>
          </div>
        </div>
        <TicketsTable rows={tickets} loading={ticketsLoading} />
      </section>

      <AskPanel />
    </div>
  );
}
