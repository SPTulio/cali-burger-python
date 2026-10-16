import { Ban, Check, ChefHat, CircleX, ClipboardCheck, PackageCheck, Truck, type LucideIcon } from "lucide-react";
import { useState } from "react";

import { Button, type ButtonProps } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { formatDateTime, formatTime } from "@/lib/format";
import { ORDER_ACTION } from "@/lib/labels";
import { cn } from "@/lib/utils";
import { useOrderAction } from "@/features/orders/use-order-action";
import type { Order, OrderAction, OrderItem, OrderStatus } from "@/types/api";

const ACTION_STYLE: Record<OrderAction, ButtonProps["variant"]> = {
  accept: "primary",
  reject: "destructive-outline",
  dispatch: "primary",
  cancel: "destructive-outline",
  complete: "primary",
};

const ACTION_ICON: Record<OrderAction, LucideIcon> = {
  accept: Check,
  reject: Ban,
  dispatch: Truck,
  cancel: CircleX,
  complete: PackageCheck,
};

/** Botões das ações permitidas (vindas do servidor), cada uma com confirmação. */
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
  const act = useOrderAction();
  if (order.available_actions.length === 0) return null;
  const config = pending ? ORDER_ACTION[pending] : null;

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
          onOpenChange={(open) => !open && setPending(null)}
          title={`${config.confirmTitle} nº ${order.id}?`}
          description={config.confirmText}
          confirmLabel={config.label}
          destructive={config.destructive}
          onConfirm={() => act.mutateAsync({ id: order.id, action: pending })}
        />
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

const STEPS: { status: OrderStatus; label: string; icon: LucideIcon }[] = [
  { status: "awaiting_acceptance", label: "Recebido", icon: ClipboardCheck },
  { status: "in_preparation", label: "Em preparação", icon: ChefHat },
  { status: "out_for_delivery", label: "A caminho", icon: Truck },
  { status: "completed", label: "Entregue", icon: PackageCheck },
];

/** Progresso do pedido com o horário de cada etapa (linha do tempo vinda do servidor). */
export function OrderProgress({ order }: { order: Order }) {
  const events = order.events ?? [];
  const at = (status: OrderStatus) => events.find((e) => e.to_status === status)?.created_at;

  if (order.status === "cancelled" || order.status === "rejected") {
    const when = at(order.status);
    return (
      <div className="flex items-center gap-3 rounded-md bg-muted p-4 text-sm">
        <CircleX className="size-5 text-muted-foreground" aria-hidden />
        <div>
          <p className="font-medium">
            {order.status === "cancelled" ? "Pedido cancelado" : "Pedido recusado pela lanchonete"}
          </p>
          <p className="text-muted-foreground">
            {when && `${formatDateTime(when)} · `}Os itens não foram cobrados do estoque.
          </p>
        </div>
      </div>
    );
  }

  const current = STEPS.findIndex((s) => s.status === order.status);
  return (
    <ol className="grid grid-cols-4 gap-2" aria-label="Andamento do pedido">
      {STEPS.map((step, index) => {
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
