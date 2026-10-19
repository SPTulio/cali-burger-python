import { useQuery } from "@tanstack/react-query";
import { ChefHat, RefreshCw, Timer } from "lucide-react";

import { ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Badge, Card, Skeleton } from "@/components/ui/primitives";
import { formatElapsed, timerLevel, type TimerLevel } from "@/features/kitchen/timer";
import { OrderActions, OrderItemsList } from "@/features/orders/components";
import { useStoreStatus } from "@/features/store/use-store-status";
import { useNow } from "@/hooks/use-debounced";
import { formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Order, OrderFilters } from "@/types/api";

const QUEUE: OrderFilters = { status: ["in_preparation"], sort: "oldest", page_size: 100 };

/** Fila da cozinha: pedidos aceitos, do mais antigo para o mais novo. Atualiza sozinha. */
export function KitchenPage() {
  const now = useNow(1_000); // o cronômetro anda a cada segundo
  const store = useStoreStatus();
  const target = store.data?.prep_time_minutes ?? 20;
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
            ? `${queue.data.total} ${queue.data.total === 1 ? "pedido" : "pedidos"} em preparação · meta de ${target} min · atualiza a cada 15 s${updatedAt ? ` (última às ${updatedAt})` : ""}`
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
            <KitchenTicket key={order.id} order={order} now={now} target={target} />
          ))}
        </div>
      )}
    </div>
  );
}

const LEVEL_STYLE: Record<TimerLevel, { ticket: string; chip: string; label: string }> = {
  on_time: { ticket: "", chip: "bg-success-soft text-success", label: "no prazo" },
  attention: {
    ticket: "border-warning/50 ring-1 ring-warning/30",
    chip: "bg-warning-soft text-warning",
    label: "perto da meta",
  },
  late: {
    ticket: "border-destructive/50 ring-1 ring-destructive/30",
    chip: "bg-destructive-soft text-destructive",
    label: "atrasado",
  },
};

function KitchenTicket({ order, now, target }: { order: Order; now: number; target: number }) {
  // Cronômetro desde que o pedido entrou na cozinha (aceite pelo balcão).
  const elapsed = (now - new Date(order.status_since).getTime()) / 1000;
  const level = timerLevel(elapsed, target);
  const style = LEVEL_STYLE[level];

  return (
    <article
      className={cn("flex flex-col rounded-lg border bg-surface shadow-xs", style.ticket)}
      aria-label={`Pedido ${order.id}, ${style.label}`}
    >
      <header className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <h2 className="tabular flex items-center gap-2 text-lg font-semibold">
            #{order.id}
            {order.fulfillment === "pickup" && <Badge tone="violet">Retirada</Badge>}
          </h2>
          <p className="text-xs text-muted-foreground">{order.customer_name}</p>
        </div>
        <span
          className={cn("tabular inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-sm font-semibold", style.chip)}
          title={`Na cozinha desde ${formatTime(order.status_since)} · meta de ${target} min`}
        >
          <Timer className="size-4" aria-hidden /> {formatElapsed(elapsed)}
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
