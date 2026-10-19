import type { Fulfillment, OrderAction, OrderStatus, Role, Sex, StockLevel } from "@/types/api";

export type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "violet" | "primary";

export const ORDER_STATUS: Record<OrderStatus, { label: string; tone: Tone; customerHint: string }> = {
  awaiting_acceptance: {
    label: "Aguardando aceitação",
    tone: "warning",
    customerHint: "A lanchonete vai confirmar seu pedido em instantes.",
  },
  in_preparation: {
    label: "Em preparação",
    tone: "info",
    customerHint: "Seu pedido está sendo preparado na cozinha.",
  },
  ready: {
    label: "Pronto",
    tone: "primary",
    customerHint: "Seu pedido está pronto.",
  },
  out_for_delivery: {
    label: "A caminho",
    tone: "violet",
    customerHint: "Saiu para entrega. Confirme quando receber.",
  },
  completed: { label: "Concluído", tone: "success", customerHint: "Pedido entregue. Bom apetite!" },
  cancelled: { label: "Cancelado", tone: "neutral", customerHint: "Pedido cancelado por você." },
  rejected: {
    label: "Recusado",
    tone: "danger",
    customerHint: "A lanchonete não pôde aceitar este pedido.",
  },
};

export const ORDER_STATUS_ORDER: OrderStatus[] = [
  "awaiting_acceptance",
  "in_preparation",
  "ready",
  "out_for_delivery",
  "completed",
  "cancelled",
  "rejected",
];

export const ORDER_ACTION: Record<
  OrderAction,
  { label: string; confirmTitle: string; confirmText: string; destructive?: boolean }
> = {
  accept: {
    label: "Aceitar",
    confirmTitle: "Aceitar pedido",
    confirmText: "O pedido vai para a fila da cozinha.",
  },
  reject: {
    label: "Recusar",
    confirmTitle: "Recusar pedido",
    confirmText: "O cliente será avisado e os ingredientes voltam para o estoque.",
    destructive: true,
  },
  ready: {
    label: "Pronto",
    confirmTitle: "Marcar como pronto",
    confirmText: "O balcão será avisado para entregar ao entregador ou ao cliente.",
  },
  dispatch: {
    label: "Saiu para entrega",
    confirmTitle: "Enviar para entrega",
    confirmText: "Confirme que o pedido saiu com o entregador.",
  },
  pick_up: {
    label: "Entregue no balcão",
    confirmTitle: "Confirmar retirada",
    confirmText: "Confirme que o cliente retirou o pedido no balcão.",
  },
  cancel: {
    label: "Cancelar pedido",
    confirmTitle: "Cancelar pedido",
    confirmText: "Tem certeza? Esta ação não pode ser desfeita.",
    destructive: true,
  },
  complete: {
    label: "Recebi meu pedido",
    confirmTitle: "Confirmar recebimento",
    confirmText: "Confirma que recebeu seu pedido?",
  },
};

export const ROLE_LABEL: Record<Role, string> = {
  customer: "Cliente",
  manager: "Balconista / dono",
  cook: "Cozinheiro",
};

export const SEX_LABEL: Record<Sex, string> = {
  male: "Masculino",
  female: "Feminino",
  other: "Outro",
};

export const STOCK_LEVEL: Record<StockLevel, { label: string; tone: Tone }> = {
  ok: { label: "OK", tone: "success" },
  low: { label: "Estoque baixo", tone: "warning" },
  out: { label: "Em falta", tone: "danger" },
};

/** Motivos sugeridos. "Outro motivo" abre um campo de texto livre. */
export const REJECT_REASONS = [
  "Item em falta",
  "Endereço fora da área de entrega",
  "Endereço incompleto ou inválido",
  "Loja fechando ou cozinha sobrecarregada",
] as const;

export const CANCEL_REASONS = [
  "Pedi por engano",
  "Quero mudar o pedido",
  "Está demorando para ser aceito",
] as const;

export const OTHER_REASON = "Outro motivo";

export const FULFILLMENT_LABEL: Record<Fulfillment, string> = {
  delivery: "Entrega",
  pickup: "Retirada no balcão",
};
