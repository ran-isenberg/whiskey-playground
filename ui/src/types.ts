// Mirror of the response contract (requirements §4).
export interface TastingNotes { nose: string; palate: string; finish: string }

export interface Whiskey {
  name: string; distillery: string; country: string; region: string; type: string;
  age: number | null; abv: number; price_tier: string; rating: number;
  flavor_profile: string[]; tasting_notes: TastingNotes;
}

export interface Match { rank: number; id: string; match_score: number; why: string; serving: string; whiskey: Whiskey }
export interface OrderLine { whiskey_id: string; name: string; quantity: number }
export interface PendingOrder { items: OrderLine[] }
export interface Order { order_id: string; status: string; items: OrderLine[] }

export interface ChatResponse {
  session_id: string; message: string; matches: Match[];
  pending_order: PendingOrder | null; order: Order | null;
}

export type ErrorCode = "INVALID_REQUEST" | "THROTTLED" | "TIMEOUT" | "AGENT_ERROR";

export class ApiError extends Error {
  constructor(public code: ErrorCode, message: string) { super(message); }
}
