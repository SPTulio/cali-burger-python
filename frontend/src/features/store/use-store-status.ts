import { useQuery } from "@tanstack/react-query";

import { storeApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";

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
