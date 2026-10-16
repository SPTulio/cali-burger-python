import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ChartColumn, CircleDollarSign, Package, ReceiptText, ShoppingBasket, TrendingUp } from "lucide-react";
import { Link, useSearchParams } from "react-router";

import { reportsApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState, PageHeader, StatCard } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { Card, CardHeader, Skeleton, Table, TD, TH, THead, TR } from "@/components/ui/primitives";
import { RevenueChart } from "@/features/reports/revenue-chart";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { SalesReport } from "@/types/api";

const PRESETS = [
  { label: "Hoje", start: () => todayIso(), end: () => todayIso() },
  { label: "7 dias", start: () => todayIso(-6), end: () => todayIso() },
  { label: "30 dias", start: () => todayIso(-29), end: () => todayIso() },
  { label: "Tudo", start: () => undefined, end: () => undefined },
];

/** Inclui os dias sem venda (valor zero) para o eixo do tempo não "pular" datas. */
function fillDays(daily: SalesReport["daily"], start?: string, end?: string) {
  const byDate = new Map(daily.map((d) => [d.date, d]));
  const first = start ?? daily[0]?.date;
  const last = end ?? daily[daily.length - 1]?.date;
  if (!first || !last) return [];
  const days = [];
  for (let t = Date.parse(`${first}T00:00:00Z`); t <= Date.parse(`${last}T00:00:00Z`); t += 86_400_000) {
    const date = new Date(t).toISOString().slice(0, 10);
    const found = byDate.get(date);
    days.push({ date, revenue: Number(found?.revenue ?? 0), orders: found?.orders ?? 0 });
    if (days.length > 366) break; // períodos muito longos: limita a um ano de colunas
  }
  return days;
}

export function ReportsPage() {
  const [params, setParams] = useSearchParams();
  const start = params.get("de") ?? undefined;
  const end = params.get("ate") ?? undefined;
  const invalid = Boolean(start && end && end < start);

  const report = useQuery({
    queryKey: queryKeys.report(start, end),
    queryFn: () => reportsApi.sales(start, end),
    enabled: !invalid,
    placeholderData: keepPreviousData,
  });

  function setPeriod(nextStart?: string, nextEnd?: string) {
    const next: Record<string, string> = {};
    if (nextStart) next.de = nextStart;
    if (nextEnd) next.ate = nextEnd;
    setParams(next, { replace: true });
  }

  const data = report.data;
  return (
    <div>
      <PageHeader
        title="Relatório de vendas"
        description="Pedidos cancelados ou recusados não entram no relatório."
      />

      <Card className="mb-6 flex flex-wrap items-end gap-3 p-4">
        <Field label="De" className="w-[calc(50%-6px)] sm:w-44">
          <Input type="date" max={todayIso()} value={start ?? ""} onChange={(e) => setPeriod(e.target.value || undefined, end)} />
        </Field>
        <Field label="Até" className="w-[calc(50%-6px)] sm:w-44" error={invalid ? "Antes da data inicial." : undefined}>
          <Input type="date" max={todayIso()} value={end ?? ""} onChange={(e) => setPeriod(start, e.target.value || undefined)} />
        </Field>
        <div className="flex flex-wrap gap-1" role="group" aria-label="Períodos rápidos">
          {PRESETS.map((preset) => {
            const selected = preset.start() === start && preset.end() === end;
            return (
              <Button
                key={preset.label}
                variant={selected ? "secondary" : "ghost"}
                aria-pressed={selected}
                onClick={() => setPeriod(preset.start(), preset.end())}
              >
                {preset.label}
              </Button>
            );
          })}
        </div>
      </Card>

      {invalid ? (
        <Card>
          <EmptyState icon={ChartColumn} title="Período inválido" description="A data final deve ser igual ou posterior à inicial." />
        </Card>
      ) : report.isPending ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : report.isError ? (
        <ErrorState error={report.error} onRetry={() => report.refetch()} />
      ) : data ? (
        <div className={cn("flex flex-col gap-6", report.isPlaceholderData && "opacity-60 transition-opacity")}>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Faturamento" value={formatCurrency(data.summary.revenue)} icon={CircleDollarSign} />
            <StatCard label="Pedidos" value={data.summary.orders} icon={ReceiptText} />
            <StatCard label="Itens vendidos" value={data.summary.items_sold} icon={ShoppingBasket} />
            <StatCard label="Ticket médio" value={formatCurrency(data.summary.average_ticket)} icon={TrendingUp} />
          </div>

          {data.summary.orders === 0 ? (
            <Card>
              <EmptyState icon={ChartColumn} title="Nenhuma venda no período" description="Escolha outro período para ver o desempenho." />
            </Card>
          ) : (
            <>
              <Card>
                <CardHeader title="Faturamento por dia" description="Passe o mouse ou use Tab sobre as colunas para ver os valores." />
                <div className="p-5">
                  <RevenueChart data={fillDays(data.daily, start, end)} />
                </div>
              </Card>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <CardHeader title="Produtos mais vendidos" />
                  <Table>
                    <THead>
                      <tr>
                        <TH>Produto</TH>
                        <TH className="text-right">Qtd.</TH>
                        <TH className="text-right">Total</TH>
                      </tr>
                    </THead>
                    <tbody>
                      {data.top_products.map((p) => (
                        <TR key={p.product_name}>
                          <TD className="font-medium">{p.product_name}</TD>
                          <TD className="tabular text-right">{p.quantity}</TD>
                          <TD className="tabular text-right">{formatCurrency(p.total)}</TD>
                        </TR>
                      ))}
                    </tbody>
                  </Table>
                </Card>
                <Card>
                  <CardHeader
                    title="Ingredientes a comprar"
                    description={`Estoque atual com ${data.low_stock_threshold} unidades ou menos (independe do período).`}
                    actions={
                      <Button asChild variant="outline" size="sm">
                        <Link to="/painel/estoque">
                          <Package /> Estoque
                        </Link>
                      </Button>
                    }
                  />
                  {data.ingredients_to_buy.length === 0 ? (
                    <p className="p-5 text-sm text-muted-foreground">Nenhum ingrediente com estoque baixo.</p>
                  ) : (
                    <Table>
                      <THead>
                        <tr>
                          <TH>Ingrediente</TH>
                          <TH className="text-right">Em estoque</TH>
                        </tr>
                      </THead>
                      <tbody>
                        {data.ingredients_to_buy.map((i) => (
                          <TR key={i.ingredient_id}>
                            <TD className="font-medium">{i.name}</TD>
                            <TD className={cn("tabular text-right", i.quantity === 0 && "font-semibold text-destructive")}>
                              {i.quantity}
                            </TD>
                          </TR>
                        ))}
                      </tbody>
                    </Table>
                  )}
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
                <Card>
                  <CardHeader title="Vendas por dia e produto" />
                  <div className="max-h-[420px] overflow-y-auto">
                    <Table>
                      <THead>
                        <tr>
                          <TH>Data</TH>
                          <TH>Produto</TH>
                          <TH className="text-right">Qtd.</TH>
                          <TH className="text-right">Valor unit.</TH>
                          <TH className="text-right">Total</TH>
                        </tr>
                      </THead>
                      <tbody>
                        {data.sales_by_day.map((row) => (
                          <TR key={`${row.date}-${row.product_name}`}>
                            <TD className="tabular whitespace-nowrap text-muted-foreground">{formatDate(row.date)}</TD>
                            <TD>{row.product_name}</TD>
                            <TD className="tabular text-right">{row.quantity}</TD>
                            <TD className="tabular text-right">{formatCurrency(row.unit_price)}</TD>
                            <TD className="tabular text-right">{formatCurrency(row.total)}</TD>
                          </TR>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                </Card>
                <Card>
                  <CardHeader title="Ingredientes usados" description="Consumo real registrado nos pedidos." />
                  <div className="max-h-[420px] overflow-y-auto">
                    {data.ingredients_used.length === 0 ? (
                      <p className="p-5 text-sm text-muted-foreground">
                        Os itens vendidos no período não têm receita cadastrada.
                      </p>
                    ) : (
                      <Table>
                        <THead>
                          <tr>
                            <TH>Ingrediente</TH>
                            <TH className="text-right">Quantidade</TH>
                          </tr>
                        </THead>
                        <tbody>
                          {data.ingredients_used.map((i) => (
                            <TR key={i.ingredient_id}>
                              <TD>{i.name}</TD>
                              <TD className="tabular text-right">{i.quantity}</TD>
                            </TR>
                          ))}
                        </tbody>
                      </Table>
                    )}
                  </div>
                </Card>
              </div>
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
