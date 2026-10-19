import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CircleCheck, MapPin, Store } from "lucide-react";
import { Link, useParams, useSearchParams } from "react-router";

import { orderingActive } from "@/features/orders/utils";
import { ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { ErrorState, StatusBadge } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, Skeleton, Table, TD, TH, THead, TR } from "@/components/ui/primitives";
import { useSession } from "@/features/auth/session";
import { OrderActions, OrderProgress } from "@/features/orders/components";
import { ReorderButton } from "@/features/orders/reorder-button";
import { useStoreStatus } from "@/features/store/use-store-status";
import { formatCurrency, formatDateTime } from "@/lib/format";
import { FULFILLMENT_LABEL, ORDER_STATUS } from "@/lib/labels";

export function OrderDetailPage({ backTo = "/pedidos" }: { backTo?: string }) {
  const id = Number(useParams().id);
  const [params] = useSearchParams();
  const session = useSession();
  const store = useStoreStatus();
  const isNew = params.get("novo") === "1";

  const order = useQuery({
    queryKey: queryKeys.order(id),
    queryFn: () => ordersApi.get(id),
    enabled: Number.isInteger(id) && id > 0,
    refetchInterval: (query) => (query.state.data && orderingActive(query.state.data.status) ? 15_000 : false),
  });

  if (order.isPending) return <Skeleton className="h-96" />;
  if (order.isError) return <ErrorState error={order.error} onRetry={() => order.refetch()} />;
  const data = order.data;

  return (
    <div className="mx-auto max-w-3xl">
      <Button asChild variant="ghost" size="sm" className="-ml-3 mb-4">
        <Link to={backTo}>
          <ArrowLeft /> Voltar
        </Link>
      </Button>

      {isNew && (
        <div
          role="status"
          className="mb-6 flex items-start gap-3 rounded-lg border border-success/30 bg-success-soft p-4 text-success"
        >
          <CircleCheck className="mt-0.5 size-5 shrink-0" aria-hidden />
          <div>
            <p className="font-semibold">Pedido realizado com sucesso!</p>
            <p className="text-sm">
              Assim que a lanchonete aceitar, ele vai para a cozinha. Esta página se atualiza sozinha.
            </p>
          </div>
        </div>
      )}

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">Pedido nº {data.id}</h1>
            <StatusBadge status={data.status} />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {formatDateTime(data.created_at)} ·{" "}
            {data.status === "ready"
              ? data.fulfillment === "pickup"
                ? "Pronto! Pode retirar no balcão."
                : "Pronto! Aguardando o entregador."
              : ORDER_STATUS[data.status].customerHint}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <OrderActions order={data} size="md" />
          {session.data?.role === "customer" && !orderingActive(data.status) && (
            <ReorderButton order={data} size="md" />
          )}
        </div>
      </div>

      <Card className="mb-6 p-5">
        <OrderProgress order={data} />
      </Card>

      <Card className="mb-6">
        <CardHeader title="Itens" />
        <Table>
          <THead>
            <tr>
              <TH>Produto</TH>
              <TH className="text-right">Qtd.</TH>
              <TH className="text-right">Preço</TH>
              <TH className="text-right">Subtotal</TH>
            </tr>
          </THead>
          <tbody>
            {data.items.map((item) => (
              <TR key={item.id}>
                <TD>
                  <span className="font-medium">{item.product_name}</span>
                  {item.notes && <span className="block text-xs text-muted-foreground">Obs.: {item.notes}</span>}
                </TD>
                <TD className="tabular text-right">{item.quantity}</TD>
                <TD className="tabular text-right">{formatCurrency(item.unit_price)}</TD>
                <TD className="tabular text-right">{formatCurrency(item.subtotal)}</TD>
              </TR>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t">
              <TD colSpan={3} className="text-right font-semibold">
                Total
              </TD>
              <TD className="tabular text-right font-semibold">{formatCurrency(data.total)}</TD>
            </tr>
          </tfoot>
        </Table>
      </Card>

      <div className="grid gap-6 sm:grid-cols-2">
        <Card className="p-5">
          <h2 className="mb-2 text-sm font-semibold">{FULFILLMENT_LABEL[data.fulfillment]}</h2>
          <p className="flex gap-2 text-sm text-muted-foreground">
            {data.fulfillment === "pickup" ? (
              <>
                <Store className="mt-0.5 size-4 shrink-0" aria-hidden />
                {store.data?.pickup_address ?? "Retire no balcão da loja."}
              </>
            ) : (
              <>
                <MapPin className="mt-0.5 size-4 shrink-0" aria-hidden />
                {data.delivery_address ?? "Endereço não registrado neste pedido."}
              </>
            )}
          </p>
        </Card>
        <Card className="p-5">
          <h2 className="mb-2 text-sm font-semibold">Pagamento</h2>
          <p className="text-sm text-muted-foreground">
            {data.payment
              ? `PIX (simulado) · ${formatCurrency(data.payment.amount)} · ${formatDateTime(data.payment.paid_at)}`
              : "Sem registro de pagamento."}
          </p>
        </Card>
      </div>
    </div>
  );
}
