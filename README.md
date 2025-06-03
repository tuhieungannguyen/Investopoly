# 🎲 Investopoly

A multiplayer educational board game simulating real-world investing and macroeconomic decision-making. Inspired by Monopoly, but with modern financial instruments and macro events.

---

## 📦 Project Structure

```

investopoly/
├── client/              # Pygame-based frontend
│   ├── main.py
│   ├── client\_socket.py
│   ├── client\_handler.py
│   ├── state\_manager.py
│   ├── lobby.py
│   └── host\_dashboard.py
│
├── server/              # FastAPI WebSocket backend
│   ├── main.py
│   ├── websocket\_router.py
│   ├── game\_controller.py
│   ├── state\_store.py
│   ├── models/
│   ├── logic/
│   └── utils/
│
├── assets/              # Game graphics (icons, tiles)
├── requirements.txt     # Python dependencies
└── README.md

````

---

## 🚀 Features

- 🎯 Roll dice to move on a 20-tile financial board
- 🏘️ Invest in stocks, real estate, and savings
- 📉 Experience macro events like Shock, Tax, and Chance
- 💰 Net Worth visualization
- 🧑‍🏫 Quizzes and financial education integration
- 🧠 Host mode to control gameplay, inject market events

---

## 🛠 Technologies Used

- Python + FastAPI for backend server
- WebSocket for real-time multiplayer
- Pygame for interactive frontend UX
- Modular OOP structure (SOLID-based)
- Threading for client-server sync
- Redis (optional future improvement)

---

<!-- ## 🧪 How to Run (Local)

### 1. Backend

```bash
cd server
pip install fastapi uvicorn
uvicorn main:app --reload
````

### 2. Frontend (Client)

```bash
cd client
pip install pygame websocket-client
python main.py
``` -->
