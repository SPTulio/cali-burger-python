import type { OrderStatus } from "@/types/api";

/** Pedido ainda em andamento (vale a pena atualizar sozinho). */
export function orderingActive(status: OrderStatus): boolean {
  return (
    status === "awaiting_acceptance" ||
    status === "in_preparation" ||
    status === "ready" ||
    status === "out_for_delivery"
  );
}
