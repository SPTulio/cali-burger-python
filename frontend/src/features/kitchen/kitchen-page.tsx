import { useQuery } from "@tanstack/react-query";
import { ChefHat, RefreshCw, Timer } from "lucide-react";

import { ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, Skeleton } from "@/components/ui/primitives";
import { OrderActions, OrderItemsList } from "@/features/orders/components";
import { useNow } from "@/hooks/use-debounced";
import { formatTime, minutesSince } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Order, OrderFilters } from "@/types/api";

const QUEUE: OrderFilters = { status: ["in_preparation"], sort: "oldest", page_size: 100 };
const LATE_AFTER_MINUTES = 20;

/** Fila da cozinha: pedidos aceitos, do mais antigo para o mais novo. Atualiza sozinha. */
export function KitchenPage() {
  const now = useNow(15_000);
  const queue = useQuery({
    queryKey: queryKeys.orders(QUEUE),
    queryFn: () => ordersApi.list(QUEUE),
    refetchInterval: 15_000,
    refetchIntervalInBackground: true,
  });

  const updatedAt = queue.dataUpdatedAt ? formatTime(new Date(queue.dataUpdatedAt).toISOString()) : null;

  return (
    <div>
      <PageHeader
        title="Fila da cozinha"
        description={
          queue.data
            ? `${queue.data.total} ${queue.data.total === 1 ? "pedido" : "pedidos"} em preparação · atualiza a cada 15 s${updatedAt ? ` (última às ${updatedAt})` : ""}`
            : "Pedidos aceitos pelo balcão, do mais antigo para o mais novo."
        }
        actions={
          <Button variant="outline" onClick={() => queue.refetch()} loading={queue.isFetching}>
            {!queue.isFetching && <RefreshCw />} Atualizar
          </Button>
        }
      />
      {queue.isPending ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      ) : queue.isError ? (
        <ErrorState error={queue.error} onRetry={() => queue.refetch()} />
      ) : queue.data.items.length === 0 ? (
        <Card>
          <EmptyState
            icon={ChefHat}
            title="Nenhum pedido na fila"
            description="Quando o balcão aceitar um pedido, ele aparece aqui automaticamente."
          />
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {queue.data.items.map((order) => (
            <KitchenTicket key={order.id} order={order} now={now} />
          ))}
        </div>
      )}
    </div>
  );
}

function KitchenTicket({ order, now }: { order: Order; now: number }) {
  // Tempo desde que o pedido foi aceito (entrou na cozinha).
  const acceptedAt = order.updated_at;
  const waiting = minutesSince(acceptedAt, now);
  const late = waiting >= LATE_AFTER_MINUTES;

  return (
    <article
      className={cn(
        "flex flex-col rounded-lg border bg-surface shadow-xs",
        late && "border-warning/50 ring-1 ring-warning/30",
      )}
      aria-label={`Pedido ${order.id}`}
    >
      <header className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <h2 className="tabular text-lg font-semibold">#{order.id}</h2>
          <p className="text-xs text-muted-foreground">{order.customer_name}</p>
        </div>
        <span
          className={cn(
            "tabular inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium",
            late ? "bg-warning-soft text-warning" : "bg-muted text-muted-foreground",
          )}
          title={`Na cozinha desde ${formatTime(acceptedAt)}`}
        >
          <Timer className="size-3.5" aria-hidden /> {waiting} min
        </span>
      </header>
      <div className="flex-1 px-4 py-3 text-base [&_li]:text-[15px]">
        <OrderItemsList items={order.items} />
      </div>
      <footer className="border-t p-3">
        <OrderActions order={order} size="lg" fullWidth />
      </footer>
    </article>
  );
}
