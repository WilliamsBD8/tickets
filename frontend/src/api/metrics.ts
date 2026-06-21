import { fetchJson } from "./client";
import type { MetricsResponse } from "../types/api";

export async function fetchMetrics(): Promise<MetricsResponse> {
  return fetchJson<MetricsResponse>("/metrics");
}
