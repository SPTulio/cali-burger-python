export type TimerLevel = "on_time" | "attention" | "late";

/** Faixas do cronômetro da cozinha a partir da meta de preparo da loja:
 *  no prazo até 75% da meta, atenção até a meta, atrasado depois dela. */
export function timerLevel(elapsedSeconds: number, targetMinutes: number): TimerLevel {
  const target = Math.max(1, targetMinutes) * 60;
  if (elapsedSeconds >= target) return "late";
  if (elapsedSeconds >= target * 0.75) return "attention";
  return "on_time";
}

/** 65 → "01:05"; 3725 → "1:02:05". */
export function formatElapsed(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const mmss = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return h > 0 ? `${h}:${mmss}` : mmss;
}
