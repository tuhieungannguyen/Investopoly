import { useMemo, useState } from "react";
import { api } from "./services/api";
import { useGameStore } from "./store/gameStore";
import ActionBar from "./components/ActionBar";
import Board from "./components/Board";
import EndGameModal from "./components/EndGameModal";
import Lobby from "./components/Lobby";
import Panels from "./components/Panels";
import QuizModal from "./components/QuizModal";
import SavingModal from "./components/SavingModal";
import styles from "./App.module.css";

function App() {
  const {
    roomId,
    playerName,
    connectionStatus,
    isHost,
    gameStarted,
    currentRound,
    currentPlayer,
    players,
    portfolio,
    leaderboard,
    notifications,
    lastRoll,
    quiz,
    savingPrompt,
    gameSummary,
    winner,
    error,
    setSession,
    connectSocket,
    setError,
    clearError
  } = useGameStore();

  const [busy, setBusy] = useState(false);

  const joined = useMemo(
    () => connectionStatus === "connected" || players.length > 0,
    [connectionStatus, players.length]
  );

  async function handleJoin(nextRoomId: string, nextPlayerName: string) {
    setBusy(true);
    clearError();
    try {
      try {
        await api.createRoom(nextRoomId, nextPlayerName);
      } catch (createError) {
        const message = createError instanceof Error ? createError.message : "";
        if (!message.toLowerCase().includes("already exists")) {
          throw createError;
        }
      }

      await api.joinRoom(nextRoomId, nextPlayerName);
      setSession(nextRoomId, nextPlayerName);
      connectSocket();
    } catch (joinError) {
      setError(joinError instanceof Error ? joinError.message : "Could not join room.");
    } finally {
      setBusy(false);
    }
  }

  if (!joined) {
    return (
      <Lobby
        busy={busy}
        error={error}
        status={connectionStatus}
        onJoin={handleJoin}
      />
    );
  }

  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.brandCluster}>
          <img src="/assets/ui/INVESTOPOLY.png" alt="Investopoly" className={styles.brand} />
          <div>
            <p className={styles.room}>Room {roomId}</p>
            <p className={styles.meta}>{playerName}</p>
          </div>
        </div>
        <div className={styles.statusCluster}>
          <span className={styles.status} data-state={connectionStatus}>
            {connectionStatus}
          </span>
          <span>Round {currentRound ?? "-"}</span>
          <span>{currentPlayer ? `${currentPlayer}'s turn` : "Waiting"}</span>
        </div>
      </header>

      {error && (
        <button className={styles.errorBanner} onClick={clearError}>
          {error}
        </button>
      )}

      <section className={styles.layout}>
        <div className={styles.boardColumn}>
          <Board players={players} currentPlayer={currentPlayer} />
        </div>
        <aside className={styles.sideColumn}>
          <Panels
            leaderboard={leaderboard}
            notifications={notifications}
            portfolio={portfolio}
            players={players}
            lastRoll={lastRoll}
          />
          <ActionBar
            isHost={isHost}
            gameStarted={gameStarted}
            roomId={roomId}
            playerName={playerName}
            currentPlayer={currentPlayer}
            lastRoll={lastRoll}
          />
        </aside>
      </section>

      {quiz && <QuizModal quiz={quiz} roomId={roomId} playerName={playerName} />}
      {savingPrompt && <SavingModal prompt={savingPrompt} />}
      {gameSummary && <EndGameModal summary={gameSummary} winner={winner} />}
    </main>
  );
}

export default App;
