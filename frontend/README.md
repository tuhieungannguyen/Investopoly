# Investopoly Web MVP

React + Vite + TypeScript frontend for the existing FastAPI backend.

## Stack

- React
- Vite
- TypeScript
- Zustand
- CSS modules
- Existing assets copied from `shared/ui` and `shared/avt`

## Run

Start the backend first from the project root:

```bash
uvicorn server.main:app --reload
```

Then run the frontend:

```bash
cd frontend
npm install
npm run dev
```

The default frontend URL is `http://localhost:5173`.

## Environment

Create `.env.local` if the backend is not on localhost:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## MVP Scope

- Create or join a room
- Connect to existing WebSocket room channel
- Show board with player avatars
- Show leaderboard, portfolio, notifications, and last roll
- Start game, roll dice, buy estate, buy one stock, withdraw savings, end turn
- Handle quiz, saving prompt, and end game modals
