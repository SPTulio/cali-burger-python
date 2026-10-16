import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { MenuItem } from "@/types/api";

/** Limite por item, igual ao do servidor (sistema original: 20). */
export const MAX_ITEM_QUANTITY = 20;
export const MAX_NOTES_LENGTH = 255;

export interface CartLine {
  menuItemId: number;
  name: string;
  price: string;
  imageUrl: string | null;
  quantity: number;
  notes: string;
}

interface CartState {
  lines: CartLine[];
  add: (item: MenuItem, quantity?: number) => number;
  setQuantity: (menuItemId: number, quantity: number) => void;
  setNotes: (menuItemId: number, notes: string) => void;
  remove: (menuItemId: number) => void;
  /** Atualiza nome/preço/foto com o cardápio atual e remove o que saiu dele. */
  sync: (menu: MenuItem[]) => string[];
  clear: () => void;
}

const clamp = (n: number) => Math.max(0, Math.min(MAX_ITEM_QUANTITY, Math.floor(n)));

// O carrinho fica no navegador (como a sessão do sistema original) e é esvaziado no logout.
export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      lines: [],
      add: (item, quantity = 1) => {
        const existing = get().lines.find((l) => l.menuItemId === item.id);
        const target = clamp((existing?.quantity ?? 0) + quantity);
        const added = target - (existing?.quantity ?? 0);
        set(({ lines }) =>
          existing
            ? { lines: lines.map((l) => (l.menuItemId === item.id ? { ...l, quantity: target } : l)) }
            : {
                lines: [
                  ...lines,
                  {
                    menuItemId: item.id,
                    name: item.name,
                    price: item.price,
                    imageUrl: item.image_url,
                    quantity: target,
                    notes: "",
                  },
                ],
              },
        );
        return added;
      },
      setQuantity: (menuItemId, quantity) =>
        set(({ lines }) => ({
          lines:
            clamp(quantity) === 0
              ? lines.filter((l) => l.menuItemId !== menuItemId)
              : lines.map((l) => (l.menuItemId === menuItemId ? { ...l, quantity: clamp(quantity) } : l)),
        })),
      setNotes: (menuItemId, notes) =>
        set(({ lines }) => ({
          lines: lines.map((l) =>
            l.menuItemId === menuItemId ? { ...l, notes: notes.slice(0, MAX_NOTES_LENGTH) } : l,
          ),
        })),
      remove: (menuItemId) =>
        set(({ lines }) => ({ lines: lines.filter((l) => l.menuItemId !== menuItemId) })),
      sync: (menu) => {
        const byId = new Map(menu.map((m) => [m.id, m]));
        const removed = get()
          .lines.filter((l) => !byId.has(l.menuItemId))
          .map((l) => l.name);
        const lines = get()
          .lines.filter((l) => byId.has(l.menuItemId))
          .map((l) => {
            const item = byId.get(l.menuItemId)!;
            return { ...l, name: item.name, price: item.price, imageUrl: item.image_url };
          });
        const changed = JSON.stringify(lines) !== JSON.stringify(get().lines);
        if (changed) set({ lines });
        return removed;
      },
      clear: () => set({ lines: [] }),
    }),
    { name: "cb-cart", storage: createJSONStorage(() => localStorage), version: 1 },
  ),
);

export function cartTotals(lines: CartLine[]) {
  // Centavos inteiros para não acumular erro de arredondamento.
  const cents = lines.reduce((sum, l) => sum + Math.round(Number(l.price) * 100) * l.quantity, 0);
  const count = lines.reduce((sum, l) => sum + l.quantity, 0);
  return { total: cents / 100, count };
}
