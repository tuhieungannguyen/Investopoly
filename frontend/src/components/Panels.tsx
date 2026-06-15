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
  const chartEntries = ranking.slice(0, 4);

  return (
    <div className={styles.grid}>
      <section className={styles.leaderboardPanel} aria-label="Leaderboard">
        <div className={styles.chart}>
          {chartEntries.map((entry, index) => {
            const percent = Math.max(24, Math.round((entry.net_worth / topNetWorth) * 100));
            return (
              <div
                className={styles.chartColumn}
                data-rank={index + 1}
                data-tooltip={`${entry.player}: current net worth ${entry.net_worth ? money.format(entry.net_worth) : "not calculated yet"}`}
                key={entry.player}
              >
                <strong>{entry.net_worth ? entry.net_worth : "-"}</strong>
                <div className={styles.avatarBar} style={{ height: `${percent}%` }}>
                  <img src={`/assets/avt/${(index % 6) + 1}.png`} alt="" aria-hidden="true" />
                </div>
                <span>{entry.player}</span>
              </div>
            );
          })}
          {Array.from({ length: Math.max(0, 4 - chartEntries.length) }).map((_, index) => (
            <div className={styles.emptySlot} key={index} aria-hidden="true" />
          ))}
        </div>
      </section>

      <section className={styles.profilePanel}>
        {portfolio ? (
          <div className={styles.portfolio}>
            <div data-tooltip="Cash available for immediate purchases and fees."><span>Cash</span><strong>{money.format(portfolio.cash)}</strong></div>
            <div data-tooltip="Owned real estate tiles."><span>Real Estate</span><strong>{portfolio.estates.join(", ") || "-"}</strong></div>
            <div data-tooltip="Stock holdings by ticker and quantity."><span>Stock</span><strong>{Object.entries(portfolio.stocks).map(([k, v]) => `${k} x${v}`).join(", ") || "-"}</strong></div>
            <div data-tooltip="Money currently deposited in savings."><span>Savings</span><strong>{money.format(portfolio.saving)}</strong></div>
            <div data-tooltip="Cash plus savings plus current asset values."><span>Net worth</span><strong>{money.format(portfolio.net_worth)}</strong></div>
            <div data-tooltip={`Current board position: ${portfolio.current_position}`}><span>Tile</span><strong>{TILE_MAP[portfolio.current_position] ?? portfolio.current_position}</strong></div>
          </div>
        ) : (
          <p className={styles.empty}>Waiting for portfolio.</p>
        )}
      </section>

      <section className={styles.rollPanel}>
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
    </div>
  );
}
