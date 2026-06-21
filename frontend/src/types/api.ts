/** Tipos alineados con la API FastAPI (JSON). */

export interface TicketRawFields {
  ticket_id: number;
  customer_name: string | null;
  customer_email: string | null;
  customer_age: number | null;
  customer_gender: string | null;
  product_purchased: string | null;
  date_of_purchase: string | null;
  purchase_date: string | null;
  ticket_type: string | null;
  ticket_subject: string | null;
  ticket_description: string | null;
  ticket_status: string | null;
  ticket_priority: string | null;
  ticket_channel: string | null;
  first_response_time: string | null;
  time_to_resolution: string | null;
  customer_satisfaction_rating: number | null;
}

export interface TicketAIFields {
  category: string | null;
  priority: string | null;
  summary: string | null;
  sentiment: string | null;
  urgency: string | null;
  suggested_team: string | null;
  model: string | null;
  analyzed_at: string | null;
}

export interface TicketEnriched {
  id: number;
  raw: TicketRawFields;
  ai: TicketAIFields | null;
}

export interface TicketListResponse {
  items: TicketEnriched[];
  total: number;
}

export interface TopCountItem {
  label: string | null;
  count: number;
}

export interface MetricsResponse {
  total_tickets: number;
  analyzed_tickets: number;
  pending_analysis: number;
  high_or_critical: number;
  by_priority: Record<string, number>;
  by_category: Record<string, number>;
  by_sentiment: Record<string, number>;
  top_products: TopCountItem[];
  top_customers: TopCountItem[];
  tickets_last_7_days: number;
}

export interface AskResponse {
  answer: string;
  model: string;
}

export interface AnalyzeTicketsResponse {
  processed: number;
  provider: string;
}

export interface TicketListQuery {
  category?: string;
  priority?: string;
  status?: string;
  sentiment?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
  analyzed_only?: boolean;
}
