import type { BoardPlayer, LeaderboardEntry, Player, RollResult } from "../types/game";
import { TILE_MAP } from "../types/constants";
import styles from "./Panels.module.css";

type Props = {
  leaderboard: LeaderboardEntry[];
  notifications: Array<{ id: number; text: string }>;
  portfolio: Player | null;
  players: BoardPlayer[];
  lastRoll: RollResult | null;
};

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

export default function Panels({ leaderboard, notifications, portfolio, players, lastRoll }: Props) {
  const ranking = leaderboard.length ? leaderboard : players.map((p) => ({ player: p.player_name, net_worth: 0 }));
  const topNetWorth = Math.max(...ranking.map((entry) => entry.net_worth), 1);

  return (
    <div className={styles.grid}>
      <section className={`${styles.panel} ${styles.leaderboardPanel}`}>
        <div className={styles.panelHeader}>
          <h2>Leaderboard</h2>
          <span>{ranking.length} players</span>
        </div>
        <div className={styles.leaderboard}>
          {ranking.map((entry, index) => {
            const percent = Math.max(6, Math.round((entry.net_worth / topNetWorth) * 100));
            return (
              <div
                className={styles.rankRow}
                data-rank={index + 1}
                data-tooltip={`${entry.player}: current net worth ${entry.net_worth ? money.format(entry.net_worth) : "not calculated yet"}`}
                key={entry.player}
              >
                <span className={styles.rankBadge}>{index + 1}</span>
                <div className={styles.rankMain}>
                  <strong>{entry.player}</strong>
                  <div className={styles.rankTrack}>
                    <i style={{ width: `${percent}%` }} />
                  </div>
                </div>
                <em>{entry.net_worth ? money.format(entry.net_worth) : "-"}</em>
              </div>
            );
          })}
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <h2>Portfolio</h2>
          <span>{portfolio ? portfolio.player_name : "waiting"}</span>
        </div>
        {portfolio ? (
          <div className={styles.portfolio}>
            <div data-tooltip="Cash available for immediate purchases and fees."><span>Cash</span><strong>{money.format(portfolio.cash)}</strong></div>
            <div data-tooltip="Money currently deposited in savings."><span>Saving</span><strong>{money.format(portfolio.saving)}</strong></div>
            <div data-tooltip="Cash plus savings plus current asset values."><span>Net worth</span><strong>{money.format(portfolio.net_worth)}</strong></div>
            <div data-tooltip={`Current board position: ${portfolio.current_position}`}><span>Tile</span><strong>{TILE_MAP[portfolio.current_position] ?? portfolio.current_position}</strong></div>
            <div className={styles.wide} data-tooltip="Stock holdings by ticker and quantity."><span>Stocks</span><strong>{Object.entries(portfolio.stocks).map(([k, v]) => `${k} x${v}`).join(", ") || "-"}</strong></div>
            <div className={styles.wide} data-tooltip="Owned real estate tiles."><span>Estates</span><strong>{portfolio.estates.join(", ") || "-"}</strong></div>
          </div>
        ) : (
          <p className={styles.empty}>Waiting for portfolio.</p>
        )}
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <h2>Last Roll</h2>
          <span>{lastRoll ? lastRoll.tile.name : "none"}</span>
        </div>
        {lastRoll ? (
          <div
            className={styles.roll}
            data-tooltip={`Tile owner: ${lastRoll.tile.owner ?? "none"} | Tile value: ${lastRoll.tile.value || "n/a"}`}
          >
            <strong>{lastRoll.dice}</strong>
            <span>{lastRoll.tile.name}</span>
            <small>{lastRoll.can_buy_estate ? "Estate available" : lastRoll.can_buy_stock ? "Stock available" : "No purchase"}</small>
          </div>
        ) : (
          <p className={styles.empty}>No roll yet.</p>
        )}
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <h2>Notifications</h2>
          <span>{notifications.length}</span>
        </div>
        <div className={styles.notifications}>
          {notifications.map((item) => (
            <p key={item.id}>{item.text}</p>
          ))}
        </div>
      </section>
    </div>
  );
}
