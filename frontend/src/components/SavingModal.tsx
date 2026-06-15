import { FormEvent, useState } from "react";
import { api } from "../services/api";
import { useGameStore } from "../store/gameStore";
import type { SavingPrompt } from "../types/game";
import styles from "./Modal.module.css";

type Props = {
  prompt: SavingPrompt;
};

export default function SavingModal({ prompt }: Props) {
  const [amount, setAmount] = useState(Math.max(0, Math.floor(prompt.max_amount / 2)).toString());
  const { closeSavingPrompt, addNotification, setError } = useGameStore();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const result = await api.depositSaving(prompt.room_id, prompt.player_name, Number(amount));
      addNotification(result.message ?? "Saving deposited.");
      closeSavingPrompt();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not deposit saving.");
    }
  }

  return (
    <div className={styles.backdrop}>
      <form className={styles.modal} onSubmit={submit}>
        <h2>Savings</h2>
        <p>{prompt.message}</p>
        <label>
          <span>Amount</span>
          <input
            type="number"
            min="1"
            max={prompt.max_amount}
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </label>
        <div className={styles.row}>
          <button className={styles.imageTextButton} type="button" onClick={closeSavingPrompt}>
            <img src="/assets/ui/button_1.png" alt="" aria-hidden="true" />
            <span>Skip</span>
          </button>
          <button className={styles.imageButton} type="submit" aria-label="Deposit">
            <img src="/assets/ui/deposit.png" alt="" aria-hidden="true" />
          </button>
        </div>
      </form>
    </div>
  );
}
