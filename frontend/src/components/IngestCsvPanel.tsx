import { useRef, useState, type FormEvent } from "react";
import { ingestTicketsCsv } from "../api/ingest";

type Props = {
  onDone: () => Promise<void>;
};

export function IngestCsvPanel({ onDone }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [replace, setReplace] = useState(true);
  const [autoAnalyze, setAutoAnalyze] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) {
      setError("Selecciona un archivo .csv");
      return;
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("El archivo debe tener extensión .csv");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const res = await ingestTicketsCsv(file, { replace, autoAnalyze: autoAnalyze });
      setMessage(
        `Importados: ${res.imported} ticket(s). Modo: ${res.replace ? "reemplazo total" : "fusión por ID"}. ` +
          `Analizados en esta petición: ${res.analyzed}.`,
      );
      if (inputRef.current) inputRef.current.value = "";
      await onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="section ingest-section" aria-labelledby="ingest-heading">
      <h2 id="ingest-heading">Subir dataset (CSV)</h2>
      <p className="muted small">
        UTF-8, mismas columnas que el CSV de la prueba (incluye <code>Ticket ID</code>).{" "}
        <strong>Reemplazar todo</strong> borra tickets y análisis actuales antes de importar.
      </p>
      <form className="ingest-form" onSubmit={onSubmit}>
        <label className="field">
          <span>Archivo</span>
          <input ref={inputRef} type="file" accept=".csv,text/csv" />
        </label>
        <label className="field checkbox-field">
          <input type="checkbox" checked={replace} onChange={(e) => setReplace(e.target.checked)} />
          <span>Reemplazar toda la base (recomendado para un CSV completo nuevo)</span>
        </label>
        <label className="field checkbox-field">
          <input type="checkbox" checked={autoAnalyze} onChange={(e) => setAutoAnalyze(e.target.checked)} />
          <span>Tras importar, ejecutar análisis IA (mock/OpenAI según backend)</span>
        </label>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Importando…" : "Importar CSV"}
        </button>
      </form>
      {error ? (
        <p className="error-banner" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="success-banner" role="status">
          {message}
        </p>
      ) : null}
    </section>
  );
}
