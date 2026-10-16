import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ChevronRight, ReceiptText } from "lucide-react";
import { Link, useSearchParams } from "react-router";

import { ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState, PageHeader, Pagination, StatusBadge } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";
import { Card, Skeleton } from "@/components/ui/primitives";
import { OrderActions } from "@/features/orders/components";
import { formatCurrency, formatDateTime, todayIso } from "@/lib/format";
import { ORDER_STATUS, ORDER_STATUS_ORDER } from "@/lib/labels";
import type { OrderFilters, OrderStatus } from "@/types/api";

const PAGE_SIZE = 10;

export function MyOrdersPage() {
  // Filtros na URL: voltar do detalhe mantém o contexto.
  const [params, setParams] = useSearchParams();
  const status = (params.get("status") as OrderStatus | null) ?? undefined;
  const start = params.get("desde") ?? undefined;
  const page = Number(params.get("pagina")) || 1;
  const filters: OrderFilters = {
    status: status ? [status] : undefined,
    start,
    page,
    page_size: PAGE_SIZE,
  };

  const orders = useQuery({
    queryKey: queryKeys.orders(filters),
    queryFn: () => ordersApi.list(filters),
    placeholderData: keepPreviousData,
    refetchInterval: 30_000, // acompanha a mudança de status sem recarregar
  });

  function update(changes: Record<string, string | undefined>) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    if (!("pagina" in changes)) next.delete("pagina");
    setParams(next, { replace: true });
  }

  const hasFilters = Boolean(status || start);

  return (
    <div>
      <PageHeader title="Meus pedidos" description="Acompanhe o andamento e o histórico dos seus pedidos." />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <Field label="Status" className="w-full sm:w-56">
          <Select value={status ?? ""} onChange={(e) => update({ status: e.target.value || undefined })}>
            <option value="">Todos</option>
            {ORDER_STATUS_ORDER.map((s) => (
              <option key={s} value={s}>
                {ORDER_STATUS[s].label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="A partir de" className="w-full sm:w-48">
          <Input type="date" max={todayIso()} value={start ?? ""} onChange={(e) => update({ desde: e.target.value || undefined })} />
        </Field>
        {hasFilters && (
          <Button variant="ghost" onClick={() => setParams({}, { replace: true })}>
            Limpar filtros
          </Button>
        )}
      </div>

      {orders.isPending ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : orders.isError ? (
        <ErrorState error={orders.error} onRetry={() => orders.refetch()} />
      ) : orders.data.items.length === 0 ? (
        <Card>
          <EmptyState
            icon={ReceiptText}
            title={hasFilters ? "Nenhum pedido com esses filtros" : "Você ainda não fez pedidos"}
            description={hasFilters ? "Ajuste ou limpe os filtros para ver outros pedidos." : "Que tal pedir agora?"}
            action={
              hasFilters ? undefined : (
                <Button asChild>
                  <Link to="/">Ver o cardápio</Link>
                </Button>
              )
            }
          />
        </Card>
      ) : (
        <Card>
          <ul className="divide-y">
            {orders.data.items.map((order) => (
              <li key={order.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:gap-6 sm:px-5">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link to={`/pedidos/${order.id}`} className="font-semibold hover:underline">
                      Pedido nº {order.id}
                    </Link>
                    <StatusBadge status={order.status} />
                  </div>
                  <p className="mt-1 truncate text-sm text-muted-foreground">
                    {order.items.map((i) => `${i.quantity}× ${i.product_name}`).join(" · ")}
                  </p>
                  <p className="tabular mt-1 text-xs text-muted-foreground">
                    {formatDateTime(order.created_at)} · {formatCurrency(order.total)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <OrderActions order={order} />
                  <Button asChild variant="ghost" size="sm">
                    <Link to={`/pedidos/${order.id}`} aria-label={`Detalhes do pedido ${order.id}`}>
                      Detalhes <ChevronRight />
                    </Link>
                  </Button>
                </div>
              </li>
            ))}
          </ul>
          <Pagination
            page={orders.data.page}
            pages={orders.data.pages}
            total={orders.data.total}
            pageSize={PAGE_SIZE}
            onPageChange={(p) => update({ pagina: String(p) })}
          />
        </Card>
      )}
    </div>
  );
}
