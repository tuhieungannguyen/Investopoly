import { FormEvent, useState } from "react";
import styles from "./Lobby.module.css";

type Props = {
  busy: boolean;
  error: string | null;
  status: string;
  onJoin: (roomId: string, playerName: string) => Promise<void>;
};

export default function Lobby({ busy, error, status, onJoin }: Props) {
  const [roomId, setRoomId] = useState("demo");
  const [playerName, setPlayerName] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onJoin(roomId.trim(), playerName.trim());
  }

  return (
    <main className={styles.lobby}>
      <form className={styles.card} onSubmit={submit}>
        <img src="/assets/ui/INVESTOPOLY.png" alt="Investopoly" className={styles.logo} />
        <label>
          <span>Room</span>
          <input
            value={roomId}
            onChange={(event) => setRoomId(event.target.value)}
            autoComplete="off"
            required
          />
        </label>
        <label>
          <span>Player</span>
          <input
            value={playerName}
            onChange={(event) => setPlayerName(event.target.value)}
            autoComplete="off"
            required
          />
        </label>
        <button className={styles.imageButton} disabled={busy || !roomId.trim() || !playerName.trim()}>
          <img src="/assets/ui/button_1.png" alt="" aria-hidden="true" />
          <span>{busy ? "Connecting" : "Join Room"}</span>
        </button>
        {error && <p className={styles.error}>{error}</p>}
      </form>
    </main>
  );
}
