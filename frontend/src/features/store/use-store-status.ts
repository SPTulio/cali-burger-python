import { useQuery } from "@tanstack/react-query";

import { storeApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import type { StoreSettingsInput, StoreStatus } from "@/types/api";

/** Loja aberta/fechada/pausada. Revalida a cada minuto: o horário muda sem ação de ninguém. */
export function useStoreStatus() {
  return useQuery({
    queryKey: queryKeys.store,
    queryFn: storeApi.status,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}

export const WEEKDAY_LABELS = [
  "Segunda",
  "Terça",
  "Quarta",
  "Quinta",
  "Sexta",
  "Sábado",
  "Domingo",
] as const;

/** "18:00:00" → "18:00" */
export function shortTime(value: string): string {
  return value.slice(0, 5);
}

/** Configurações atuais no formato de envio (cada cartão altera só os seus campos). */
export function settingsInput(status: StoreStatus): StoreSettingsInput {
  return {
    prep_time_minutes: status.prep_time_minutes,
    pickup_address: status.pickup_address,
    delivery_time_minutes: status.delivery_time_minutes,
    default_delivery_fee: status.default_delivery_fee,
    free_delivery_above: status.free_delivery_above,
  };
}

/** "6,50" ou "6.50" -> "6.50"; vazio -> null. */
export function moneyInput(value: string): string | null {
  const normalized = value.trim().replace(",", ".");
  return normalized === "" ? null : normalized;
}
