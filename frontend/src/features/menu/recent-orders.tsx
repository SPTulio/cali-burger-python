import { useQuery } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";
import { useState } from "react";

import { ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { Button } from "@/components/ui/button";
import { useReorder } from "@/features/cart/reorder";
import { formatCurrency, formatDateTime } from "@/lib/format";
import type { Order, OrderFilters } from "@/types/api";

const RECENT: OrderFilters = { page_size: 10 };

/** Assinatura dos itens: pedidos iguais aparecem uma vez só. */
function signature(order: Order) {
  return order.items
    .map((i) => `${i.menu_item_id}:${i.quantity}`)
    .sort()
    .join("|");
}

/** "Peça de novo": os últimos pedidos diferentes do cliente, repetidos em um toque. */
export function RecentOrders({ onReordered }: { onReordered: () => void }) {
  const orders = useQuery({ queryKey: queryKeys.orders(RECENT), queryFn: () => ordersApi.list(RECENT) });
  const reorder = useReorder();
  const [busy, setBusy] = useState<number | null>(null);

  const seen = new Set<string>();
  const recent = (orders.data?.items ?? [])
    .filter((o) => o.items.some((i) => i.menu_item_id !== null))
    .filter((o) => {
      const key = signature(o);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 3);
  if (recent.length === 0) return null;

  async function repeat(order: Order) {
    setBusy(order.id);
    try {
      if (await reorder(order)) onReordered();
    } finally {
      setBusy(null);
    }
  }

  return (
    <section aria-labelledby="peca-de-novo" className="mb-8">
      <h2 id="peca-de-novo" className="mb-3 text-lg font-semibold">
        Peça de novo
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {recent.map((order) => (
          <div key={order.id} className="flex flex-col gap-3 rounded-lg border bg-surface p-4 shadow-xs">
            <div className="min-w-0">
              <p className="line-clamp-2 text-sm font-medium">
                {order.items.map((i) => `${i.quantity}× ${i.product_name}`).join(", ")}
              </p>
              <p className="tabular mt-1 text-xs text-muted-foreground">
                Pedido nº {order.id} · {formatDateTime(order.created_at)} · {formatCurrency(order.total)}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-auto self-start"
              loading={busy === order.id}
              onClick={() => repeat(order)}
            >
              {busy !== order.id && <RotateCcw />} Repetir pedido
            </Button>
          </div>
        ))}
      </div>
    </section>
  );
}
