import { postJson } from "./client";
import type { AskResponse } from "../types/api";

export async function askTickets(question: string): Promise<AskResponse> {
  return postJson<AskResponse>("/ask", { question });
}
