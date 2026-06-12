export const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export const WS_BASE_URL =
  import.meta.env.VITE_WS_URL?.replace(/\/$/, "") ?? "ws://localhost:8000";
