import { API_BASE_URL } from "./config";
import type { ApiResult, GameSummary, RollResult } from "../types/game";

type JsonValue = Record<string, unknown>;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const message = data?.detail ?? data?.error ?? response.statusText;
    throw new Error(String(message));
  }

  return data as T;
}

function post<T>(path: string, body: JsonValue): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export const api = {
  createRoom: (room_id: string, host_name: string) =>
    post<{ message: string }>("/create", { room_id, host_name }),

  joinRoom: (room_id: string, player_name: string) =>
    post<{ message: string }>("/join", { room_id, player_name }),

  startGame: (room_id: string) =>
    post<{ message: string }>("/start", { room_id }),

  rollDice: (room_id: string, player_name: string) =>
    post<RollResult>("/roll", { room_id, player_name }),

  endTurn: (room_id: string, player_name: string) =>
    post<{ message: string }>("/end_turn", { room_id, player_name }),

  buyEstate: (room_id: string, player_name: string) =>
    post<ApiResult>("/buy_estate", { room_id, player_name }),

  buyStock: (room_id: string, player_name: string, amount: number) =>
    post<{ message: string }>("/buy_stock", { room_id, player_name, amount }),

  depositSaving: (room_id: string, player_name: string, amount: number) =>
    post<ApiResult>("/api/saving/deposit", { room_id, player_name, amount }),

  withdrawSaving: (room_id: string, player_name: string) =>
    post<ApiResult>("/api/saving/withdraw", { room_id, player_name }),

  submitQuizAnswer: (room_id: string, player_name: string, question_id: number, answer_index: number) =>
    post<{ correct: boolean }>("/quiz/answer", { room_id, player_name, question_id, answer_index }),

  endGame: (room_id: string) =>
    post<{ message: string; results: GameSummary }>("/end", { room_id }),

  getStatus: (room_id: string) =>
    request<{ round: number; current_player: string; players: Record<string, unknown> }>(`/status/${room_id}`)
};
