import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ChartColumn, ClipboardList, Inbox, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState, PageHeader, Pagination, StatusBadge, TableSkeleton } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/menu";
import { Badge, Card, Table, TD, TH, THead, TR } from "@/components/ui/primitives";
import { OrderActions, OrderItemsList } from "@/features/orders/components";
import { useDebounced, useNow } from "@/hooks/use-debounced";
import { formatCurrency, formatDateTime, formatRelative, todayIso } from "@/lib/format";
import { ORDER_STATUS, ORDER_STATUS_ORDER } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { Order, OrderFilters, OrderStatus } from "@/types/api";

const PAGE_SIZE = 20;

export function ManageOrdersPage() {
  const [params, setParams] = useSearchParams();
  const visao = params.get("visao");
  const view = visao === "todos" || visao === "prontos" ? visao : "aguardando";
  const summary = useQuery({ queryKey: queryKeys.ordersSummary, queryFn: ordersApi.summary, refetchInterval: 20_000 });
  const pending = summary.data?.counts.awaiting_acceptance;
  const ready = summary.data?.counts.ready;

  return (
    <div>
      <PageHeader
        title="Pedidos"
        description="Aceite os novos pedidos e acompanhe todos os anteriores."
        actions={
          <Button asChild variant="outline">
            <Link to="/painel/relatorios">
              <ChartColumn /> Relatório de vendas
            </Link>
          </Button>
        }
      />
      <Tabs value={view} onValueChange={(v) => setParams(v === "aguardando" ? {} : { visao: v }, { replace: true })}>
        <TabsList className="mb-4">
          <TabsTrigger value="aguardando">
            Aguardando aceitação
            {pending ? (
              <span className="tabular rounded-full bg-primary px-1.5 text-[11px] font-semibold text-primary-foreground">
                {pending}
              </span>
            ) : null}
          </TabsTrigger>
          <TabsTrigger value="prontos">
            Prontos
            {ready ? (
              <span className="tabular rounded-full bg-primary px-1.5 text-[11px] font-semibold text-primary-foreground">
                {ready}
              </span>
            ) : null}
          </TabsTrigger>
          <TabsTrigger value="todos">Todos os pedidos</TabsTrigger>
        </TabsList>
      </Tabs>
      {view === "aguardando" && (
        <Queue
          status="awaiting_acceptance"
          emptyTitle="Nenhum pedido aguardando"
          emptyDescription="Novos pedidos aparecem aqui automaticamente, do mais antigo para o mais novo."
        />
      )}
      {view === "prontos" && (
        <Queue
          status="ready"
          emptyTitle="Nenhum pedido pronto"
          emptyDescription="Quando a cozinha marcar um pedido como pronto, ele aparece aqui para sair para entrega ou ser entregue no balcão."
        />
      )}
      {view === "todos" && <AllOrders />}
    </div>
  );
}

function Queue({
  status,
  emptyTitle,
  emptyDescription,
}: {
  status: OrderStatus;
  emptyTitle: string;
  emptyDescription: string;
}) {
  const filters: OrderFilters = { status: [status], sort: "oldest", page_size: 100 };
  const orders = useQuery({
    queryKey: queryKeys.orders(filters),
    queryFn: () => ordersApi.list(filters),
    refetchInterval: 15_000,
  });
  const now = useNow();

  if (orders.isPending) return <Card><TableSkeleton rows={3} columns={6} /></Card>;
  if (orders.isError) return <ErrorState error={orders.error} onRetry={() => orders.refetch()} />;
  if (orders.data.items.length === 0) {
    return (
      <Card>
        <EmptyState icon={Inbox} title={emptyTitle} description={emptyDescription} />
      </Card>
    );
  }
  return (
    <Card>
      <OrdersTable orders={orders.data.items} now={now} showRelative />
    </Card>
  );
}

function AllOrders() {
  const [params, setParams] = useSearchParams();
  const status = (params.get("status") as OrderStatus | null) ?? undefined;
  const start = params.get("de") ?? undefined;
  const end = params.get("ate") ?? undefined;
  const page = Number(params.get("pagina")) || 1;
  const [search, setSearch] = useState(params.get("busca") ?? "");
  const q = useDebounced(search.trim());

  function update(changes: Record<string, string | undefined>) {
    const next = new URLSearchParams(params);
    next.set("visao", "todos");
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    if (!("pagina" in changes)) next.delete("pagina");
    setParams(next, { replace: true });
  }

  useEffect(() => {
    if ((params.get("busca") ?? "") !== q) update({ busca: q || undefined });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const filters: OrderFilters = {
    status: status ? [status] : undefined,
    start,
    end,
    q: q || undefined,
    page,
    page_size: PAGE_SIZE,
  };
  const orders = useQuery({
    queryKey: queryKeys.orders(filters),
    queryFn: () => ordersApi.list(filters),
    placeholderData: keepPreviousData,
    refetchInterval: 30_000,
  });
  const invalidPeriod = Boolean(start && end && end < start);
  const hasFilters = Boolean(status || start || end || q);

  return (
    <Card>
      <div className="flex flex-wrap items-end gap-3 border-b p-4">
        <Field label="Buscar" className="w-full sm:w-64">
          <div className="relative">
            <Search className="pointer-events-none absolute top-2.5 left-3 size-4 text-muted-foreground" aria-hidden />
            <Input
              className="pl-9"
              placeholder="Nº do pedido ou cliente"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </Field>
        <Field label="Status" className="w-full sm:w-52">
          <Select value={status ?? ""} onChange={(e) => update({ status: e.target.value || undefined })}>
            <option value="">Todos</option>
            {ORDER_STATUS_ORDER.map((s) => (
              <option key={s} value={s}>
                {ORDER_STATUS[s].label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="De" className="w-[calc(50%-6px)] sm:w-40">
          <Input type="date" max={todayIso()} value={start ?? ""} onChange={(e) => update({ de: e.target.value || undefined })} />
        </Field>
        <Field label="Até" className="w-[calc(50%-6px)] sm:w-40" error={invalidPeriod ? "Antes da data inicial." : undefined}>
          <Input type="date" max={todayIso()} value={end ?? ""} onChange={(e) => update({ ate: e.target.value || undefined })} />
        </Field>
        {hasFilters && (
          <Button
            variant="ghost"
            onClick={() => {
              setSearch("");
              setParams({ visao: "todos" }, { replace: true });
            }}
          >
            Limpar filtros
          </Button>
        )}
      </div>
      {invalidPeriod ? (
        <EmptyState icon={ClipboardList} title="Período inválido" description="A data final deve ser igual ou posterior à inicial." />
      ) : orders.isPending ? (
        <TableSkeleton rows={6} columns={6} />
      ) : orders.isError ? (
        <ErrorState error={orders.error} onRetry={() => orders.refetch()} />
      ) : orders.data.items.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="Nenhum pedido encontrado"
          description={hasFilters ? "Ajuste os filtros para ver mais pedidos." : "Os pedidos dos clientes aparecem aqui."}
        />
      ) : (
        <>
          <div className={orders.isPlaceholderData ? "opacity-60 transition-opacity" : undefined}>
            <OrdersTable orders={orders.data.items} />
          </div>
          <Pagination
            page={orders.data.page}
            pages={orders.data.pages}
            total={orders.data.total}
            pageSize={PAGE_SIZE}
            onPageChange={(p) => update({ pagina: String(p) })}
          />
        </>
      )}
    </Card>
  );
}

function OrdersTable({ orders, now, showRelative }: { orders: Order[]; now?: number; showRelative?: boolean }) {
  return (
    <Table>
      <THead>
        <tr>
          <TH className="w-20">Nº</TH>
          <TH>Cliente</TH>
          <TH className="min-w-48">Itens e observações</TH>
          <TH className="text-right">Total</TH>
          {!showRelative && <TH>Status</TH>}
          <TH className={showRelative ? undefined : "hidden xl:table-cell"}>Data</TH>
          <TH className="text-right">
            <span className="sr-only">Ações</span>
          </TH>
        </tr>
      </THead>
      <tbody>
        {orders.map((order) => (
          <TR key={order.id}>
            <TD>
              <Link to={`/painel/pedidos/${order.id}`} className="tabular font-semibold text-primary hover:underline">
                #{order.id}
              </Link>
            </TD>
            <TD className="whitespace-nowrap">
              {order.customer_name}
              {order.fulfillment === "pickup" && (
                <Badge tone="violet" className="ml-2">
                  Retirada
                </Badge>
              )}
              {!showRelative && (
                <span className="tabular block text-xs text-muted-foreground xl:hidden">
                  {formatDateTime(order.created_at)}
                </span>
              )}
            </TD>
            <TD>
              <OrderItemsList items={order.items} />
            </TD>
            <TD className="tabular text-right font-medium whitespace-nowrap">{formatCurrency(order.total)}</TD>
            {!showRelative && (
              <TD>
                <StatusBadge status={order.status} />
                {order.status_reason && (
                  <span className="mt-1 block max-w-48 text-xs text-muted-foreground">{order.status_reason}</span>
                )}
              </TD>
            )}
            <TD
              className={cn(
                "tabular whitespace-nowrap text-muted-foreground",
                !showRelative && "hidden xl:table-cell",
              )}
            >
              {formatDateTime(order.created_at)}
              {showRelative && (
                <span className="block text-xs">
                  {order.status === "ready" ? "pronto " : ""}
                  {formatRelative(order.status_since, now)}
                </span>
              )}
            </TD>
            <TD className="text-right">
              <OrderActions order={order} className="flex-nowrap justify-end" />
            </TD>
          </TR>
        ))}
      </tbody>
    </Table>
  );
}
