import { create } from "zustand";
import { WS_BASE_URL } from "../services/config";
import type {
  BoardPlayer,
  GameEvent,
  GameSummary,
  LeaderboardEntry,
  Player,
  QuizPrompt,
  RollResult,
  SavingPrompt
} from "../types/game";

type Notification = {
  id: number;
  text: string;
};

type ConnectionStatus = "idle" | "connecting" | "connected" | "disconnected" | "error";

type GameState = {
  roomId: string;
  playerName: string;
  connectionStatus: ConnectionStatus;
  isHost: boolean;
  gameStarted: boolean;
  currentRound: number | null;
  currentPlayer: string | null;
  players: BoardPlayer[];
  portfolio: Player | null;
  leaderboard: LeaderboardEntry[];
  notifications: Notification[];
  lastRoll: RollResult | null;
  quiz: QuizPrompt | null;
  savingPrompt: SavingPrompt | null;
  gameSummary: GameSummary | null;
  winner: string | null;
  error: string | null;
  ws: WebSocket | null;
  setSession: (roomId: string, playerName: string) => void;
  connectSocket: () => void;
  disconnectSocket: () => void;
  handleEvent: (event: GameEvent) => void;
  addNotification: (text: string) => void;
  clearError: () => void;
  setError: (message: string | null) => void;
  setLastRoll: (roll: RollResult | null) => void;
  closeQuiz: () => void;
  closeSavingPrompt: () => void;
};

let notificationId = 0;

function eventText(event: GameEvent): string | null {
  if (typeof event.message === "string") {
    return event.message;
  }

  switch (event.type) {
    case "leaderboard_update":
    case "portfolio_update":
    case "update_positions":
      return null;
    case "player_joined":
      return `${event.player} joined ${event.players.length > 1 ? "the room" : "the table"}.`;
    case "quiz_question":
      return "Quiz prompt opened.";
    default:
      return event.type.replaceAll("_", " ");
  }
}

export const useGameStore = create<GameState>((set, get) => ({
  roomId: "",
  playerName: "",
  connectionStatus: "idle",
  isHost: false,
  gameStarted: false,
  currentRound: null,
  currentPlayer: null,
  players: [],
  portfolio: null,
  leaderboard: [],
  notifications: [],
  lastRoll: null,
  quiz: null,
  savingPrompt: null,
  gameSummary: null,
  winner: null,
  error: null,
  ws: null,

  setSession: (roomId, playerName) => {
    set({ roomId, playerName });
  },

  connectSocket: () => {
    const { roomId, playerName, ws } = get();
    if (!roomId || !playerName) {
      set({ error: "Room and player name are required." });
      return;
    }

    ws?.close();
    set({ connectionStatus: "connecting", error: null });

    const socket = new WebSocket(`${WS_BASE_URL}/ws/${encodeURIComponent(roomId)}/${encodeURIComponent(playerName)}`);

    socket.onopen = () => {
      set({ connectionStatus: "connected" });
      get().addNotification("Connected to room.");
    };

    socket.onmessage = (message) => {
      try {
        get().handleEvent(JSON.parse(message.data) as GameEvent);
      } catch {
        get().addNotification("Received an unreadable realtime message.");
      }
    };

    socket.onclose = () => {
      set((state) => ({
        connectionStatus: state.connectionStatus === "error" ? "error" : "disconnected",
        ws: null
      }));
    };

    socket.onerror = () => {
      set({ connectionStatus: "error", error: "WebSocket connection failed." });
    };

    set({ ws: socket });
  },

  disconnectSocket: () => {
    get().ws?.close();
    set({ ws: null, connectionStatus: "disconnected" });
  },

  handleEvent: (event) => {
    const text = eventText(event);
    if (text) {
      get().addNotification(text);
    }

    switch (event.type) {
      case "player_joined": {
        const currentPlayerName = get().playerName;
        set({
          players: event.players,
          portfolio: event.portfolio,
          leaderboard: event.leaderboard,
          isHost: event.players[0]?.player_name === currentPlayerName
        });
        break;
      }

      case "game_started":
        set({
          gameStarted: true,
          currentRound: event.round,
          currentPlayer: event.current_player,
          gameSummary: null,
          winner: null
        });
        break;

      case "next_turn":
        set({
          currentRound: event.round,
          currentPlayer: event.current_player
        });
        break;

      case "new_round_started":
        set({
          currentRound: event.current_round,
          currentPlayer: event.current_player
        });
        break;

      case "player_rolled":
        set({
          lastRoll: {
            message: event.message,
            dice: event.dice,
            tile: event.tile,
            can_buy_estate: event.can_buy_estate,
            can_buy_stock: event.can_buy_stock
          }
        });
        break;

      case "update_positions":
        set({ players: event.players });
        break;

      case "leaderboard_update":
        set({ leaderboard: event.leaderboard });
        break;

      case "portfolio_update":
        set({ portfolio: event.portfolio });
        break;

      case "quiz_question":
        set({
          quiz: {
            question_id: event.question_id,
            question: event.question,
            options: event.options
          }
        });
        break;

      case "saving_prompt":
        set({
          savingPrompt: {
            message: event.message,
            max_amount: event.max_amount,
            room_id: event.room_id,
            player_name: event.player_name
          }
        });
        break;

      case "game_ended": {
        const summary = event.final_results ?? {
          leaderboard: event.leaderboard ?? [],
          summary: event.summary ?? []
        };
        set({
          gameSummary: summary,
          winner: event.winner ?? summary.leaderboard[0]?.player ?? null,
          gameStarted: false
        });
        break;
      }

      case "room_reset":
      case "server_reset":
        set({
          gameStarted: false,
          currentRound: null,
          currentPlayer: null,
          players: [],
          portfolio: null,
          leaderboard: [],
          lastRoll: null,
          quiz: null,
          savingPrompt: null,
          gameSummary: null,
          winner: null
        });
        break;
    }
  },

  addNotification: (text) => {
    set((state) => ({
      notifications: [{ id: ++notificationId, text }, ...state.notifications].slice(0, 18)
    }));
  },

  clearError: () => set({ error: null }),
  setError: (message) => set({ error: message }),
  setLastRoll: (roll) => set({ lastRoll: roll }),
  closeQuiz: () => set({ quiz: null }),
  closeSavingPrompt: () => set({ savingPrompt: null })
}));
