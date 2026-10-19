import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { storeApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { ErrorState } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Field, FormError, Input } from "@/components/ui/field";
import { Card, CardHeader, Skeleton } from "@/components/ui/primitives";
import { moneyInput, settingsInput } from "@/features/store/use-store-status";
import type { DeliveryZone, StoreStatus } from "@/types/api";

interface ZoneRow {
  name: string;
  fee: string;
  extra_minutes: string;
  is_active: boolean;
}

const toRow = (z: DeliveryZone): ZoneRow => ({
  name: z.name,
  fee: z.fee.replace(".", ","),
  extra_minutes: String(z.extra_minutes),
  is_active: z.is_active,
});

/** Bairros atendidos com taxa e tempo extra, taxa padrão e frete grátis. */
export function DeliveryCard({ status }: { status: StoreStatus }) {
  const zones = useQuery({ queryKey: queryKeys.zones, queryFn: storeApi.zones });
  if (zones.isPending) return <Skeleton className="h-64" />;
  if (zones.isError) return <ErrorState error={zones.error} onRetry={() => zones.refetch()} />;
  return <DeliveryForm key={JSON.stringify(zones.data)} zones={zones.data} status={status} />;
}

function DeliveryForm({ zones, status }: { zones: DeliveryZone[]; status: StoreStatus }) {
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<ZoneRow[]>(() => zones.map(toRow));
  const [travel, setTravel] = useState(String(status.delivery_time_minutes));
  const [defaultFee, setDefaultFee] = useState(status.default_delivery_fee?.replace(".", ",") ?? "");
  const [freeAbove, setFreeAbove] = useState(status.free_delivery_above?.replace(".", ",") ?? "");
  const [error, setError] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: async () => {
      await storeApi.replaceZones(
        rows
          .filter((r) => r.name.trim())
          .map((r) => ({
            name: r.name.trim(),
            fee: moneyInput(r.fee) ?? "0",
            extra_minutes: Number(r.extra_minutes) || 0,
            is_active: r.is_active,
          })),
      );
      return storeApi.updateSettings({
        ...settingsInput(status),
        delivery_time_minutes: Number(travel) || 0,
        default_delivery_fee: moneyInput(defaultFee),
        free_delivery_above: moneyInput(freeAbove),
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.store, data);
      queryClient.invalidateQueries({ queryKey: queryKeys.zones });
      setError(null);
      toast.success("Configurações de entrega salvas.");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const setRow = (index: number, change: Partial<ZoneRow>) =>
    setRows((all) => all.map((r, i) => (i === index ? { ...r, ...change } : r)));

  return (
    <Card>
      <CardHeader
        title="Entrega"
        description="Sem bairros cadastrados e sem taxa padrão, a entrega é grátis para qualquer endereço. Os nomes são comparados sem acentos e sem diferenciar maiúsculas."
      />
      <div className="flex flex-col gap-5 p-5">
        <FormError message={error} />
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Deslocamento base (min)" description="Somado ao preparo na previsão.">
            <Input type="number" min={0} max={180} value={travel} onChange={(e) => setTravel(e.target.value)} />
          </Field>
          <Field label="Taxa para outros bairros (R$)" description="Vazio: só os bairros da lista.">
            <Input inputMode="decimal" placeholder="—" value={defaultFee} onChange={(e) => setDefaultFee(e.target.value)} />
          </Field>
          <Field label="Frete grátis a partir de (R$)" description="Vazio: sem frete grátis.">
            <Input inputMode="decimal" placeholder="—" value={freeAbove} onChange={(e) => setFreeAbove(e.target.value)} />
          </Field>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium">Bairros atendidos</p>
          {rows.length === 0 && <p className="text-sm text-muted-foreground">Nenhum bairro cadastrado.</p>}
          {rows.length > 0 && (
            <div className="mb-1 hidden grid-cols-[1fr_96px_80px_64px_36px] gap-2 text-xs text-muted-foreground sm:grid">
              <span>Bairro</span>
              <span>Taxa (R$)</span>
              <span>+ min</span>
              <span>Ativo</span>
            </div>
          )}
          <div className="flex flex-col gap-2">
            {rows.map((row, index) => (
              <div key={index} className="grid grid-cols-[1fr_96px_80px_64px_36px] items-center gap-2">
                <Input
                  placeholder="Bairro"
                  value={row.name}
                  maxLength={100}
                  onChange={(e) => setRow(index, { name: e.target.value })}
                  aria-label="Bairro"
                />
                <Input
                  inputMode="decimal"
                  value={row.fee}
                  onChange={(e) => setRow(index, { fee: e.target.value })}
                  aria-label={`Taxa de ${row.name || "entrega"} em reais`}
                />
                <Input
                  type="number"
                  min={0}
                  max={180}
                  value={row.extra_minutes}
                  onChange={(e) => setRow(index, { extra_minutes: e.target.value })}
                  aria-label={`Minutos extras para ${row.name || "o bairro"}`}
                />
                <input
                  type="checkbox"
                  className="size-4 justify-self-center accent-[var(--primary)]"
                  checked={row.is_active}
                  onChange={(e) => setRow(index, { is_active: e.target.checked })}
                  aria-label={`Entregar em ${row.name || "este bairro"}`}
                />
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => setRows((all) => all.filter((_, i) => i !== index))}
                  aria-label={`Remover ${row.name || "bairro"}`}
                >
                  <Trash className="text-muted-foreground" />
                </Button>
              </div>
            ))}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2"
            onClick={() => setRows((all) => [...all, { name: "", fee: "5,00", extra_minutes: "0", is_active: true }])}
          >
            <Plus /> Adicionar bairro
          </Button>
        </div>

        <div className="flex justify-end">
          <Button onClick={() => save.mutate()} loading={save.isPending}>
            Salvar entrega
          </Button>
        </div>
      </div>
    </Card>
  );
}
