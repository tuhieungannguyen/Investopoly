export type Player = {
  player_name: string;
  current_position: number;
  cash: number;
  stocks: Record<string, number>;
  estates: string[];
  saving: number;
  net_worth: number;
  round_played: number;
  pending_bonus: string[];
};

export type BoardPlayer = {
  player_name: string;
  current_position: number;
};

export type LeaderboardEntry = {
  player: string;
  net_worth: number;
};

export type Tile = {
  name: string;
  owner: string | null;
  value: number;
};

export type Stock = {
  name: string;
  owner_list: string[];
  industry: string;
  start_price: number;
  now_price: number;
  service_fee: number;
  position: number;
  available_units: number;
  max_per_player: number;
};

export type QuizPrompt = {
  question_id: number;
  question: string;
  options: string[];
};

export type SavingPrompt = {
  message: string;
  max_amount: number;
  room_id: string;
  player_name: string;
};

export type RollResult = {
  message: string;
  dice: number;
  tile: Tile;
  can_buy_estate: boolean;
  can_buy_stock: boolean;
};

export type GameSummary = {
  leaderboard: Array<LeaderboardEntry & {
    cash?: number;
    saving?: number;
    stock_value?: number;
    estate_count?: number;
  }>;
  summary: unknown[];
};

export type GameEvent = {
  type: string;
  [key: string]: any;
};

export type ApiResult<T = unknown> = T & {
  success?: boolean;
  message?: string;
};
