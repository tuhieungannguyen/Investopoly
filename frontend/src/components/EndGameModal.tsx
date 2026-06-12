import type { GameSummary } from "../types/game";
import styles from "./Modal.module.css";

type Props = {
  summary: GameSummary;
  winner: string | null;
};

export default function EndGameModal({ summary, winner }: Props) {
  return (
    <div className={styles.backdrop}>
      <section className={styles.modal}>
        <h2>Game Finished</h2>
        <p>{winner ? `${winner} wins` : "Final results"}</p>
        <div className={styles.table}>
          {summary.leaderboard.map((entry, index) => (
            <div key={entry.player}>
              <span>{index + 1}</span>
              <strong>{entry.player}</strong>
              <em>${entry.net_worth.toFixed(0)}</em>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
