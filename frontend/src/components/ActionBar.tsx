import { useState } from "react";
import { api } from "../services/api";
import { useGameStore } from "../store/gameStore";
import type { RollResult } from "../types/game";
import styles from "./ActionBar.module.css";

type Props = {
  isHost: boolean;
  gameStarted: boolean;
  roomId: string;
  playerName: string;
  currentPlayer: string | null;
  lastRoll: RollResult | null;
};

export default function ActionBar({ isHost, gameStarted, roomId, playerName, currentPlayer, lastRoll }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const { setError, addNotification, setLastRoll } = useGameStore();
  const isTurn = currentPlayer === playerName;

  async function run(label: string, action: () => Promise<void>) {
    setBusy(label);
    setError(null);
    try {
      await action();
    } catch (error) {
      setError(error instanceof Error ? error.message : `${label} failed.`);
    } finally {
      setBusy(null);
    }
  }

  function imageLabel(label: string, src: string) {
    return (
      <>
        <img src={src} alt="" aria-hidden="true" />
        <span className={styles.srOnly}>{label}</span>
      </>
    );
  }

  return (
    <section className={styles.actions}>
      {!gameStarted && isHost && (
        <button
          className={`${styles.imageButton} ${styles.wide}`}
          data-tooltip="Host starts the game and sets the first active turn."
          disabled={busy !== null}
          aria-label="Start game"
          onClick={() => run("start", async () => {
            const result = await api.startGame(roomId);
            addNotification(result.message);
          })}
        >
          {imageLabel("Start game", "/assets/ui/start.png")}
        </button>
      )}

      {gameStarted && (
        <>
          <button
            className={styles.imageButton}
            data-tooltip={isTurn ? "Roll the dice for your current turn." : "Only the current player can roll."}
            disabled={!isTurn || busy !== null}
            aria-label="Roll dice"
            onClick={() => run("roll", async () => {
              const roll = await api.rollDice(roomId, playerName);
              setLastRoll(roll);
              addNotification(`${playerName} rolled ${roll.dice}.`);
            })}
          >
            {imageLabel("Roll dice", "/assets/ui/roll.png")}
          </button>
          <button
            className={styles.imageButton}
            data-tooltip={lastRoll?.can_buy_estate ? "Buy the estate on your current tile." : "Roll onto an unowned estate first."}
            disabled={!lastRoll?.can_buy_estate || busy !== null}
            aria-label="Buy estate"
            onClick={() => run("buy estate", async () => {
              const result = await api.buyEstate(roomId, playerName);
              addNotification(result.message ?? "Estate purchased.");
            })}
          >
            {imageLabel("Buy estate", "/assets/ui/buy.png")}
          </button>
          <button
            className={styles.imageButton}
            data-tooltip={lastRoll?.can_buy_stock ? "Buy one stock unit from the bank." : "Roll onto a stock tile with available units first."}
            disabled={!lastRoll?.can_buy_stock || busy !== null}
            aria-label="Buy stock"
            onClick={() => run("buy stock", async () => {
              const result = await api.buyStock(roomId, playerName, 1);
              addNotification(result.message);
            })}
          >
            {imageLabel("Buy stock", "/assets/ui/buy.png")}
          </button>
          <button
            className={styles.imageTextButton}
            data-tooltip="Withdraw all available savings. Matured savings include interest."
            disabled={busy !== null}
            aria-label="Withdraw savings"
            onClick={() => run("withdraw", async () => {
              const result = await api.withdrawSaving(roomId, playerName);
              addNotification(result.message ?? "Saving withdrawn.");
            })}
          >
            <img src="/assets/ui/button_1.png" alt="" aria-hidden="true" />
            <span>Withdraw</span>
          </button>
          <button
            className={`${styles.imageButton} ${styles.wide}`}
            data-tooltip={isTurn ? "Pass control to the next player." : "Only the current player can end this turn."}
            disabled={!isTurn || busy !== null}
            aria-label="End turn"
            onClick={() => run("end turn", async () => {
              const result = await api.endTurn(roomId, playerName);
              addNotification(result.message);
              setLastRoll(null);
            })}
          >
            {imageLabel("End turn", "/assets/ui/end.png")}
          </button>
        </>
      )}
    </section>
  );
}
