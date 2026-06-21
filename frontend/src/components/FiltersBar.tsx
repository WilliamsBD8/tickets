import type { TicketListQuery } from "../types/api";

type Props = {
  draft: TicketListQuery;
  onChange: (next: TicketListQuery) => void;
  onApply: () => void;
  onReset: () => void;
  analyzing: boolean;
  onAnalyze: () => void;
};

const PRIORITIES = ["", "low", "medium", "high", "critical"] as const;
const SENTIMENTS = ["", "positive", "neutral", "negative"] as const;

export function FiltersBar({ draft, onChange, onApply, onReset, analyzing, onAnalyze }: Props) {
  const set = (patch: Partial<TicketListQuery>) => onChange({ ...draft, ...patch });

  return (
    <section className="section filters-section" aria-labelledby="filters-heading">
      <div className="section-head">
        <h2 id="filters-heading">Filtros</h2>
        <div className="btn-row">
          <button type="button" className="btn btn-primary" onClick={onApply}>
            Aplicar
          </button>
          <button type="button" className="btn btn-secondary" onClick={onReset}>
            Limpiar
          </button>
          <button type="button" className="btn btn-outline" onClick={onAnalyze} disabled={analyzing}>
            {analyzing ? "Analizando…" : "Analizar pendientes (IA)"}
          </button>
        </div>
      </div>
      <div className="filters-grid">
        <label className="field">
          <span>Búsqueda</span>
          <input
            type="search"
            placeholder="Asunto, descripción, producto, cliente…"
            value={draft.search ?? ""}
            onChange={(e) => set({ search: e.target.value })}
          />
        </label>
        <label className="field">
          <span>Categoría (IA o tipo)</span>
          <input
            type="text"
            placeholder="Texto parcial"
            value={draft.category ?? ""}
            onChange={(e) => set({ category: e.target.value })}
          />
        </label>
        <label className="field">
          <span>Prioridad efectiva</span>
          <select value={draft.priority ?? ""} onChange={(e) => set({ priority: e.target.value || undefined })}>
            {PRIORITIES.map((p) => (
              <option key={p || "any"} value={p}>
                {p === "" ? "Todas" : p}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Estado</span>
          <input
            type="text"
            placeholder="Ej. open, closed…"
            value={draft.status ?? ""}
            onChange={(e) => set({ status: e.target.value })}
          />
        </label>
        <label className="field">
          <span>Sentimiento (IA)</span>
          <select value={draft.sentiment ?? ""} onChange={(e) => set({ sentiment: e.target.value || undefined })}>
            {SENTIMENTS.map((s) => (
              <option key={s || "any"} value={s}>
                {s === "" ? "Todos" : s}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Desde (compra)</span>
          <input type="date" value={draft.date_from ?? ""} onChange={(e) => set({ date_from: e.target.value || undefined })} />
        </label>
        <label className="field">
          <span>Hasta (compra)</span>
          <input type="date" value={draft.date_to ?? ""} onChange={(e) => set({ date_to: e.target.value || undefined })} />
        </label>
        <label className="field checkbox-field">
          <span>Solo con análisis IA</span>
          <input
            type="checkbox"
            checked={Boolean(draft.analyzed_only)}
            onChange={(e) => set({ analyzed_only: e.target.checked })}
          />
        </label>
      </div>
    </section>
  );
}
