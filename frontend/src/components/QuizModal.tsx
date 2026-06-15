import { api } from "../services/api";
import { useGameStore } from "../store/gameStore";
import type { QuizPrompt } from "../types/game";
import styles from "./Modal.module.css";

type Props = {
  quiz: QuizPrompt;
  roomId: string;
  playerName: string;
};

export default function QuizModal({ quiz, roomId, playerName }: Props) {
  const { closeQuiz, addNotification, setError } = useGameStore();

  async function answer(index: number) {
    try {
      const result = await api.submitQuizAnswer(roomId, playerName, quiz.question_id, index);
      addNotification(result.correct ? "Quiz answered correctly." : "Quiz answered incorrectly.");
      closeQuiz();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not submit quiz answer.");
    }
  }

  return (
    <div className={styles.backdrop}>
      <section className={styles.modal}>
        <h2>Quiz</h2>
        <p>{quiz.question}</p>
        <div className={styles.optionGrid}>
          {quiz.options.map((option, index) => (
            <button className={styles.choiceButton} key={option} onClick={() => answer(index)}>
              <img src="/assets/ui/choice.png" alt="" aria-hidden="true" />
              <span>{option}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
