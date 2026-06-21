import { useState } from "react";
import { askTickets } from "../api/ask";

export function AskPanel() {
  const [question, setQuestion] = useState(
    "¿Qué producto genera más tickets y cuáles son las prioridades más frecuentes?",
  );
  const [answer, setAnswer] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    const q = question.trim();
    if (q.length < 3) {
      setError("Escribe al menos 3 caracteres.");
      return;
    }
    setLoading(true);
    setError(null);
    setAnswer(null);
    setModel(null);
    try {
      const res = await askTickets(q);
      setAnswer(res.answer);
      setModel(res.model);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="section ask-section" aria-labelledby="ask-heading">
      <h2 id="ask-heading">Preguntar (lenguaje natural)</h2>
      <p className="muted small">
        Usa el endpoint <code>/ask</code>: combina métricas agregadas y la base de conocimiento del backend.
      </p>
      <textarea
        className="ask-input"
        rows={3}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ej.: ¿cuáles son los problemas más críticos esta semana?"
      />
      <div className="btn-row">
        <button type="button" className="btn btn-primary" onClick={submit} disabled={loading}>
          {loading ? "Pensando…" : "Enviar pregunta"}
        </button>
      </div>
      {error ? (
        <p className="error-banner" role="alert">
          {error}
        </p>
      ) : null}
      {answer ? (
        <div className="ask-response">
          {model ? (
            <p className="muted small">
              Modelo: <code>{model}</code>
            </p>
          ) : null}
          <div className="ask-answer-body">{answer}</div>
        </div>
      ) : null}
    </section>
  );
}
