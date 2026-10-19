import {
  Ban,
  BellRing,
  Check,
  ChefHat,
  CircleX,
  ClipboardCheck,
  HandPlatter,
  PackageCheck,
  Truck,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

import { Button, type ButtonProps } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Field, Input, Select } from "@/components/ui/field";
import { formatDateTime, formatTime } from "@/lib/format";
import { CANCEL_REASONS, ORDER_ACTION, OTHER_REASON, REJECT_REASONS } from "@/lib/labels";
import { cn } from "@/lib/utils";
import { useOrderAction } from "@/features/orders/use-order-action";
import type { Fulfillment, Order, OrderAction, OrderItem, OrderStatus } from "@/types/api";

const ACTION_STYLE: Record<OrderAction, ButtonProps["variant"]> = {
  accept: "primary",
  reject: "destructive-outline",
  ready: "primary",
  dispatch: "primary",
  pick_up: "primary",
  cancel: "destructive-outline",
  complete: "primary",
};

const ACTION_ICON: Record<OrderAction, LucideIcon> = {
  accept: Check,
  reject: Ban,
  ready: BellRing,
  dispatch: Truck,
  pick_up: HandPlatter,
  cancel: CircleX,
  complete: PackageCheck,
};

/** Botões das ações permitidas (vindas do servidor), cada uma com confirmação. */
function ReasonField({
  action,
  choice,
  text,
  error,
  onChoice,
  onText,
}: {
  action: "reject" | "cancel";
  choice: string;
  text: string;
  error: string | null;
  onChoice: (value: string) => void;
  onText: (value: string) => void;
}) {
  const options = action === "reject" ? REJECT_REASONS : CANCEL_REASONS;
  const required = action === "reject";
  return (
    <div className="flex flex-col gap-3">
      <Field
        label={required ? "Motivo (o cliente verá esta mensagem)" : "Motivo (opcional)"}
        error={choice !== OTHER_REASON ? (error ?? undefined) : undefined}
      >
        <Select value={choice} onChange={(e) => onChoice(e.target.value)}>
          <option value="">{required ? "Selecione o motivo" : "Prefiro não informar"}</option>
          {options.map((reason) => (
            <option key={reason} value={reason}>
              {reason}
            </option>
          ))}
          <option value={OTHER_REASON}>{OTHER_REASON}</option>
        </Select>
      </Field>
      {choice === OTHER_REASON && (
        <Field label="Descreva o motivo" error={error ?? undefined}>
          <Input maxLength={255} value={text} onChange={(e) => onText(e.target.value)} autoFocus />
        </Field>
      )}
    </div>
  );
}

export function OrderActions({
  order,
  size = "sm",
  className,
  fullWidth,
}: {
  order: Order;
  size?: ButtonProps["size"];
  className?: string;
  fullWidth?: boolean;
}) {
  const [pending, setPending] = useState<OrderAction | null>(null);
  const [choice, setChoice] = useState("");
  const [text, setText] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);
  const act = useOrderAction();
  if (order.available_actions.length === 0) return null;
  const config = pending ? ORDER_ACTION[pending] : null;
  const asksReason = pending === "reject" || pending === "cancel";

  function close() {
    setPending(null);
    setChoice("");
    setText("");
    setReasonError(null);
  }

  async function confirm(action: OrderAction) {
    const reason = (choice === OTHER_REASON ? text : choice).trim() || null;
    if (action === "reject" && !reason) {
      setReasonError("Informe o motivo da recusa.");
      throw new Error("motivo obrigatório"); // mantém o diálogo aberto
    }
    await act.mutateAsync({ id: order.id, action, reason });
  }

  return (
    <div className={cn("flex flex-wrap gap-2", fullWidth && "[&>button]:flex-1", className)}>
      {order.available_actions.map((action) => {
        const Icon = ACTION_ICON[action];
        return (
          <Button key={action} size={size} variant={ACTION_STYLE[action]} onClick={() => setPending(action)}>
            <Icon /> {ORDER_ACTION[action].label}
          </Button>
        );
      })}
      {config && pending && (
        <ConfirmDialog
          open
          onOpenChange={(open) => !open && close()}
          title={`${config.confirmTitle} nº ${order.id}?`}
          description={config.confirmText}
          confirmLabel={config.label}
          destructive={config.destructive}
          onConfirm={() => confirm(pending)}
        >
          {asksReason && (
            <ReasonField
              action={pending}
              choice={choice}
              text={text}
              error={reasonError}
              onChoice={(value) => {
                setChoice(value);
                setReasonError(null);
              }}
              onText={(value) => {
                setText(value);
                setReasonError(null);
              }}
            />
          )}
        </ConfirmDialog>
      )}
    </div>
  );
}

export function OrderItemsList({ items, showNotes = true }: { items: OrderItem[]; showNotes?: boolean }) {
  return (
    <ul className="flex flex-col gap-1.5">
      {items.map((item) => (
        <li key={item.id} className="text-sm">
          <span className="tabular font-medium">{item.quantity}×</span> {item.product_name}
          {showNotes && item.notes && (
            <span className="mt-0.5 block rounded bg-warning-soft px-2 py-1 text-xs text-warning">
              {item.notes}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

type Step = { status: OrderStatus; label: string; icon: LucideIcon };

const STEPS: Record<Fulfillment, Step[]> = {
  delivery: [
    { status: "awaiting_acceptance", label: "Recebido", icon: ClipboardCheck },
    { status: "in_preparation", label: "Em preparação", icon: ChefHat },
    { status: "ready", label: "Pronto", icon: BellRing },
    { status: "out_for_delivery", label: "A caminho", icon: Truck },
    { status: "completed", label: "Entregue", icon: PackageCheck },
  ],
  pickup: [
    { status: "awaiting_acceptance", label: "Recebido", icon: ClipboardCheck },
    { status: "in_preparation", label: "Em preparação", icon: ChefHat },
    { status: "ready", label: "Pronto para retirar", icon: BellRing },
    { status: "completed", label: "Retirado", icon: HandPlatter },
  ],
};

/** Progresso do pedido com o horário de cada etapa (linha do tempo vinda do servidor). */
export function OrderProgress({ order }: { order: Order }) {
  const events = order.events ?? [];
  const at = (status: OrderStatus) => events.find((e) => e.to_status === status)?.created_at;

  if (order.status === "cancelled" || order.status === "rejected") {
    const when = at(order.status);
    return (
      <div className="flex items-start gap-3 rounded-md bg-muted p-4 text-sm">
        <CircleX className="size-5 text-muted-foreground" aria-hidden />
        <div>
          <p className="font-medium">
            {order.status === "cancelled" ? "Pedido cancelado" : "Pedido recusado pela lanchonete"}
          </p>
          {order.status_reason && <p className="mt-0.5">Motivo: {order.status_reason}</p>}
          <p className="text-muted-foreground">
            {when && `${formatDateTime(when)} · `}Os ingredientes voltaram ao estoque da loja.
          </p>
        </div>
      </div>
    );
  }

  const steps = STEPS[order.fulfillment];
  const current = steps.findIndex((s) => s.status === order.status);
  return (
    <ol
      className={cn("grid gap-2", steps.length === 5 ? "grid-cols-5" : "grid-cols-4")}
      aria-label="Andamento do pedido"
    >
      {steps.map((step, index) => {
        const done = index <= current;
        const time = at(step.status);
        const Icon = step.icon;
        return (
          <li key={step.status} className="flex flex-col items-center gap-2 text-center" aria-current={index === current ? "step" : undefined}>
            <div className="relative flex w-full items-center justify-center">
              {index > 0 && (
                <span
                  className={cn(
                    "absolute top-1/2 right-1/2 h-0.5 w-full -translate-y-1/2",
                    index <= current ? "bg-primary" : "bg-border",
                  )}
                  aria-hidden
                />
              )}
              <span
                className={cn(
                  "relative flex size-9 items-center justify-center rounded-full border-2",
                  done ? "border-primary bg-primary text-primary-foreground" : "border-border bg-surface text-muted-foreground",
                  index === current && order.status !== "completed" && "ring-4 ring-primary/15",
                )}
              >
                <Icon className="size-4" aria-hidden />
              </span>
            </div>
            <span className={cn("text-xs font-medium", done ? "text-foreground" : "text-muted-foreground")}>
              {step.label}
            </span>
            <span className="tabular -mt-1.5 text-[11px] text-muted-foreground">{time ? formatTime(time) : " "}</span>
          </li>
        );
      })}
    </ol>
  );
}
