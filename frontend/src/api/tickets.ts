import { fetchJson, postJson } from "./client";
import type { AnalyzeTicketsResponse, TicketListQuery, TicketListResponse } from "../types/api";

function buildTicketsPath(query: TicketListQuery): string {
  const q = new URLSearchParams();
  if (query.category?.trim()) q.set("category", query.category.trim());
  if (query.priority?.trim()) q.set("priority", query.priority.trim().toLowerCase());
  if (query.status?.trim()) q.set("status", query.status.trim());
  if (query.sentiment?.trim()) q.set("sentiment", query.sentiment.trim().toLowerCase());
  if (query.search?.trim()) q.set("search", query.search.trim());
  if (query.date_from) q.set("date_from", query.date_from);
  if (query.date_to) q.set("date_to", query.date_to);
  q.set("page", String(query.page ?? 1));
  q.set("page_size", String(query.page_size ?? 50));
  if (query.analyzed_only) q.set("analyzed_only", "true");
  const s = q.toString();
  return s ? `/tickets?${s}` : "/tickets";
}

export async function fetchTickets(query: TicketListQuery): Promise<TicketListResponse> {
  return fetchJson<TicketListResponse>(buildTicketsPath(query));
}

export async function triggerAnalyze(limit = 500): Promise<AnalyzeTicketsResponse> {
  return postJson<AnalyzeTicketsResponse>("/tickets/analyze", { limit });
}
