import type { TicketEnriched } from "../types/api";

function cell(text: string | null | undefined, max = 48): { short: string; full: string } {
  const full = text ?? "—";
  const t = full.trim() || "—";
  return { short: t.length > max ? `${t.slice(0, max)}…` : t, full: t };
}

type Props = {
  rows: TicketEnriched[];
  loading: boolean;
};

export function TicketsTable({ rows, loading }: Props) {
  if (loading && rows.length === 0) {
    return (
      <div className="table-wrap muted" role="status">
        Cargando tickets…
      </div>
    );
  }

  return (
    <div className="table-wrap" role="region" aria-label="Tabla de tickets">
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Asunto</th>
            <th>Estado</th>
            <th>Producto</th>
            <th>Prioridad (IA)</th>
            <th>Categoría (IA)</th>
            <th>Sentimiento</th>
            <th>Equipo sugerido</th>
            <th>Compra</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => {
            const subj = cell(t.raw.ticket_subject, 40);
            const sum = cell(t.ai?.summary, 36);
            return (
              <tr key={t.id}>
                <td className="num">{t.id}</td>
                <td>
                  <span title={subj.full}>{subj.short}</span>
                  {t.ai?.summary ? (
                    <div className="subline" title={sum.full}>
                      {sum.short}
                    </div>
                  ) : null}
                </td>
                <td>{t.raw.ticket_status ?? "—"}</td>
                <td>{cell(t.raw.product_purchased, 28).short}</td>
                <td>{t.ai?.priority ?? t.raw.ticket_priority ?? "—"}</td>
                <td>{cell(t.ai?.category ?? t.raw.ticket_type, 28).short}</td>
                <td>
                  <span className={`pill pill-${(t.ai?.sentiment ?? "none").toLowerCase()}`}>
                    {t.ai?.sentiment ?? "—"}
                  </span>
                </td>
                <td>{t.ai?.suggested_team ?? "—"}</td>
                <td className="nowrap">{t.raw.purchase_date ?? t.raw.date_of_purchase ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {rows.length === 0 && !loading ? <p className="muted empty-hint">No hay resultados con los filtros actuales.</p> : null}
    </div>
  );
}
