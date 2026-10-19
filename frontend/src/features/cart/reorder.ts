import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { catalogApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { MAX_ITEM_QUANTITY, useCart } from "@/features/cart/store";
import type { MenuItem, Order } from "@/types/api";

export interface ReorderPlan {
  lines: { item: MenuItem; quantity: number; notes: string }[];
  /** Itens que não podem ser pedidos agora (saíram do cardápio, esgotaram ou estão pausados). */
  skipped: string[];
  /** Itens com quantidade reduzida pelo estoque atual. */
  reduced: string[];
}

/** Monta o carrinho a partir de um pedido antigo usando o cardápio **atual**: preço, nome e
 *  disponibilidade de hoje, não os do pedido. */
export function planReorder(order: Order, menu: MenuItem[], inCart: Record<number, number> = {}): ReorderPlan {
  const byId = new Map(menu.map((m) => [m.id, m]));
  const plan: ReorderPlan = { lines: [], skipped: [], reduced: [] };
  for (const line of order.items) {
    const item = line.menu_item_id !== null ? byId.get(line.menu_item_id) : undefined;
    if (!item || item.availability === "sold_out" || item.availability === "paused") {
      plan.skipped.push(line.product_name);
      continue;
    }
    const limit = Math.min(MAX_ITEM_QUANTITY, item.portions ?? MAX_ITEM_QUANTITY) - (inCart[item.id] ?? 0);
    const quantity = Math.min(line.quantity, Math.max(0, limit));
    if (quantity <= 0) {
      plan.skipped.push(line.product_name);
      continue;
    }
    if (quantity < line.quantity) plan.reduced.push(item.name);
    plan.lines.push({ item, quantity, notes: line.notes ?? "" });
  }
  return plan;
}

/** Repete um pedido: busca o cardápio atual, adiciona ao carrinho e avisa o que ficou de fora.
 *  Retorna true se algum item foi adicionado. */
export function useReorder() {
  const queryClient = useQueryClient();
  const add = useCart((s) => s.add);
  const setNotes = useCart((s) => s.setNotes);

  return async (order: Order): Promise<boolean> => {
    let menu: MenuItem[];
    try {
      menu = await queryClient.fetchQuery({ queryKey: queryKeys.menu(), queryFn: () => catalogApi.menu() });
    } catch {
      toast.error("Não foi possível carregar o cardápio. Tente novamente.");
      return false;
    }
    const inCart = Object.fromEntries(useCart.getState().lines.map((l) => [l.menuItemId, l.quantity]));
    const plan = planReorder(order, menu, inCart);
    for (const { item, quantity, notes } of plan.lines) {
      add(item, quantity);
      if (notes) setNotes(item.id, notes);
    }

    if (plan.lines.length === 0) {
      toast.error("Nenhum item deste pedido está disponível agora.");
      return false;
    }
    const warnings = [
      plan.skipped.length ? `Indisponível agora: ${plan.skipped.join(", ")}.` : null,
      plan.reduced.length ? `Quantidade ajustada ao estoque: ${plan.reduced.join(", ")}.` : null,
    ].filter(Boolean);
    if (warnings.length) toast.warning(`Itens adicionados ao carrinho. ${warnings.join(" ")}`);
    else toast.success("Itens do pedido adicionados ao carrinho.");
    return true;
  };
}
