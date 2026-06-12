import type { BoardPlayer } from "../types/game";
import { TILE_MAP } from "../types/constants";
import styles from "./Board.module.css";

type Props = {
  players: BoardPlayer[];
  currentPlayer: string | null;
};

const TILE_CENTERS = [
  { left: 10.8, top: 89.2 },
  { left: 10.8, top: 71.2 },
  { left: 10.8, top: 56.8 },
  { left: 10.8, top: 42.4 },
  { left: 10.8, top: 27.9 },
  { left: 10.8, top: 10.8 },
  { left: 28.8, top: 10.8 },
  { left: 43.2, top: 10.8 },
  { left: 57.6, top: 10.8 },
  { left: 72.1, top: 10.8 },
  { left: 89.2, top: 10.8 },
  { left: 89.2, top: 28.8 },
  { left: 89.2, top: 43.2 },
  { left: 89.2, top: 57.6 },
  { left: 89.2, top: 72.1 },
  { left: 89.2, top: 89.2 },
  { left: 71.2, top: 89.2 },
  { left: 56.8, top: 89.2 },
  { left: 42.4, top: 89.2 },
  { left: 27.9, top: 89.2 }
];

function tilePosition(position: number) {
  return TILE_CENTERS[position] ?? TILE_CENTERS[0];
}

export default function Board({ players, currentPlayer }: Props) {
  return (
    <div className={styles.boardWrap}>
      <div className={styles.boardSurface} aria-label="Investopoly board">
        {players.map((player, index) => {
          const position = Number(player.current_position) || 0;
          const coords = tilePosition(position);
          const offsetX = (index % 2) * 16 - 8;
          const offsetY = Math.floor(index / 2) * 16 - 8;
          return (
            <div
              className={styles.token}
              data-active={player.player_name === currentPlayer}
              data-tooltip={`${player.player_name} is on ${TILE_MAP[position] ?? "Unknown"} (${position})`}
              key={player.player_name}
              style={{
                left: `${coords.left}%`,
                top: `${coords.top}%`,
                transform: `translate(calc(-50% + ${offsetX}px), calc(-50% + ${offsetY}px))`
              }}
            >
              <img src={`/assets/avt/${(index % 6) + 1}.png`} alt={player.player_name} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
