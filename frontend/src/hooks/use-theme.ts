import { create } from "zustand";

type Theme = "light" | "dark";

function apply(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
  try {
    localStorage.setItem("cb-theme", theme);
  } catch {
    // Navegação privada: o tema só não fica salvo.
  }
}

/** Tema compartilhado por todos os botões de tema (o valor inicial vem do script do index.html). */
export const useTheme = create<{ theme: Theme; toggle: () => void }>((set, get) => ({
  theme: document.documentElement.classList.contains("dark") ? "dark" : "light",
  toggle: () => {
    const theme = get().theme === "dark" ? "light" : "dark";
    apply(theme);
    set({ theme });
  },
}));
