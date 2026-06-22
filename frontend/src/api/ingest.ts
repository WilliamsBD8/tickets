import { apiUrl } from "./client";
import type { IngestCsvResponse } from "../types/api";

export async function ingestTicketsCsv(
  file: File,
  opts: { replace?: boolean; autoAnalyze?: boolean },
): Promise<IngestCsvResponse> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("replace", String(opts.replace ?? true));
  fd.append("auto_analyze", String(opts.autoAnalyze ?? false));

  const res = await fetch(apiUrl("/tickets/ingest"), {
    method: "POST",
    body: fd,
  });

  const text = await res.text();
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 400)}`);
  }
  return JSON.parse(text) as IngestCsvResponse;
}
