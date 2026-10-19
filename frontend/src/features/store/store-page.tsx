import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CirclePause, CirclePlay, Copy, Plus, Trash } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { storeApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { ErrorState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Field, FormError, Input } from "@/components/ui/field";
import { Badge, Card, CardHeader, Skeleton } from "@/components/ui/primitives";
import { shortTime, useStoreStatus, WEEKDAY_LABELS } from "@/features/store/use-store-status";
import type { StoreStatus } from "@/types/api";

export function StorePage() {
  const store = useStoreStatus();

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Loja e horários"
        description="Quando a loja está fechada ou pausada, os clientes veem o aviso e não conseguem finalizar pedidos."
      />
      {store.isPending ? (
        <Skeleton className="h-96" />
      ) : store.isError ? (
        <ErrorState error={store.error} onRetry={() => store.refetch()} />
      ) : (
        <div className="flex flex-col gap-6">
          <PauseCard status={store.data} />
          <HoursCard key={JSON.stringify(store.data.hours)} status={store.data} />
          <SettingsCard key={`${store.data.prep_time_minutes}-${store.data.pickup_address}`} status={store.data} />
        </div>
      )}
    </div>
  );
}

function useSaveStore() {
  const queryClient = useQueryClient();
  return (data: StoreStatus) => queryClient.setQueryData(queryKeys.store, data);
}

function PauseCard({ status }: { status: StoreStatus }) {
  const save = useSaveStore();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const pause = useMutation({
    mutationFn: ({ paused, msg }: { paused: boolean; msg: string | null }) => storeApi.setPause(paused, msg),
    onSuccess: (data) => {
      save(data);
      toast.success(data.is_paused ? "Pedidos pausados." : "Pedidos retomados.");
      setOpen(false);
      setMessage("");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const badge = status.is_paused ? (
    <Badge tone="warning" dot>Pausada</Badge>
  ) : status.within_hours ? (
    <Badge tone="success" dot>Aberta agora</Badge>
  ) : (
    <Badge tone="neutral" dot>Fechada pelo horário</Badge>
  );

  return (
    <Card>
      <CardHeader
        title={<span className="flex items-center gap-2">Recebimento de pedidos {badge}</span>}
        description={
          status.is_paused
            ? `Aviso para os clientes: “${status.message}”`
            : "Pause quando a cozinha estiver sobrecarregada ou faltar algo essencial."
        }
        actions={
          status.is_paused ? (
            <Button onClick={() => pause.mutate({ paused: false, msg: null })} loading={pause.isPending}>
              <CirclePlay /> Retomar pedidos
            </Button>
          ) : (
            <Button variant="outline" onClick={() => setOpen(true)}>
              <CirclePause /> Pausar pedidos
            </Button>
          )
        }
      />
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader
            title="Pausar pedidos"
            description="Os clientes continuam vendo o cardápio, mas não conseguem finalizar pedidos até você retomar."
          />
          <Field label="Aviso para os clientes (opcional)" description="Ex.: Voltamos às 20h.">
            <Input maxLength={255} value={message} onChange={(e) => setMessage(e.target.value)} />
          </Field>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancelar
            </Button>
            <Button
              loading={pause.isPending}
              onClick={() => pause.mutate({ paused: true, msg: message.trim() || null })}
            >
              Pausar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

interface Slot {
  weekday: number;
  opens_at: string;
  closes_at: string;
}

function HoursCard({ status }: { status: StoreStatus }) {
  const save = useSaveStore();
  const [slots, setSlots] = useState<Slot[]>(() =>
    status.hours.map((h) => ({ weekday: h.weekday, opens_at: shortTime(h.opens_at), closes_at: shortTime(h.closes_at) })),
  );
  const [error, setError] = useState<string | null>(null);
  const update = useMutation({
    mutationFn: () => storeApi.replaceHours(slots),
    onSuccess: (data) => {
      save(data);
      setError(null);
      toast.success("Horário de funcionamento salvo.");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const setSlot = (index: number, change: Partial<Slot>) =>
    setSlots((all) => all.map((s, i) => (i === index ? { ...s, ...change } : s)));
  const copyMondayToAll = () => {
    const monday = slots.filter((s) => s.weekday === 0);
    setSlots(WEEKDAY_LABELS.flatMap((_, day) => monday.map((s) => ({ ...s, weekday: day }))));
  };

  return (
    <Card>
      <CardHeader
        title="Horário de funcionamento"
        description="Sem nenhuma faixa cadastrada, a loja fica aberta o tempo todo. Se o fechamento for antes da abertura, a faixa termina no dia seguinte (ex.: 18:00–02:00)."
      />
      <div className="flex flex-col gap-1 p-5">
        <FormError message={error} />
        {WEEKDAY_LABELS.map((label, day) => {
          const daySlots = slots.map((s, index) => ({ s, index })).filter(({ s }) => s.weekday === day);
          return (
            <div key={label} className="grid gap-2 border-b py-3 last:border-0 sm:grid-cols-[110px_1fr]">
              <span className="pt-1.5 text-sm font-medium">{label}</span>
              <div className="flex flex-col gap-2">
                {daySlots.length === 0 && <span className="pt-1.5 text-sm text-muted-foreground">Fechado</span>}
                {daySlots.map(({ s, index }) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      type="time"
                      className="w-32"
                      value={s.opens_at}
                      onChange={(e) => setSlot(index, { opens_at: e.target.value })}
                      aria-label={`${label}: abre às`}
                    />
                    <span className="text-sm text-muted-foreground">até</span>
                    <Input
                      type="time"
                      className="w-32"
                      value={s.closes_at}
                      onChange={(e) => setSlot(index, { closes_at: e.target.value })}
                      aria-label={`${label}: fecha às`}
                    />
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setSlots((all) => all.filter((_, i) => i !== index))}
                      aria-label={`Remover faixa de ${label}`}
                    >
                      <Trash className="text-muted-foreground" />
                    </Button>
                  </div>
                ))}
                <div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSlots((all) => [...all, { weekday: day, opens_at: "18:00", closes_at: "23:00" }])}
                  >
                    <Plus /> Adicionar faixa
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
        <div className="mt-3 flex flex-wrap justify-between gap-2">
          <Button variant="outline" onClick={copyMondayToAll} disabled={!slots.some((s) => s.weekday === 0)}>
            <Copy /> Copiar segunda para todos os dias
          </Button>
          <Button onClick={() => update.mutate()} loading={update.isPending}>
            Salvar horários
          </Button>
        </div>
      </div>
    </Card>
  );
}

function SettingsCard({ status }: { status: StoreStatus }) {
  const save = useSaveStore();
  const [minutes, setMinutes] = useState(String(status.prep_time_minutes));
  const [pickup, setPickup] = useState(status.pickup_address ?? "");
  const value = Number(minutes);
  const invalid = !Number.isInteger(value) || value < 1 || value > 240;
  const update = useMutation({
    mutationFn: () => storeApi.updateSettings(value, pickup.trim() || null),
    onSuccess: (data) => {
      save(data);
      toast.success("Configurações salvas.");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
  return (
    <Card>
      <CardHeader title="Preparo e retirada" />
      <form
        className="grid gap-4 p-5 sm:grid-cols-[180px_1fr]"
        onSubmit={(e) => {
          e.preventDefault();
          if (!invalid) update.mutate();
        }}
      >
        <Field
          label="Meta de preparo (min)"
          error={invalid ? "Informe de 1 a 240 minutos." : undefined}
          description="Base do tempo estimado e das cores do cronômetro da cozinha."
        >
          <Input type="number" min={1} max={240} value={minutes} onChange={(e) => setMinutes(e.target.value)} />
        </Field>
        <Field
          label="Endereço para retirada no balcão"
          description="Deixe em branco para oferecer só entrega."
        >
          <Input maxLength={255} value={pickup} onChange={(e) => setPickup(e.target.value)} placeholder="Rua, número – bairro" />
        </Field>
        <div className="flex justify-end sm:col-span-2">
          <Button type="submit" variant="outline" loading={update.isPending} disabled={invalid}>
            Salvar
          </Button>
        </div>
      </form>
    </Card>
  );
}
