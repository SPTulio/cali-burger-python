import { CirclePause, Clock } from "lucide-react";

import { useStoreStatus } from "@/features/store/use-store-status";

/** Faixa informando que a loja não aceita pedidos agora (fechada ou pausada). */
export function StoreBanner() {
  const store = useStoreStatus();
  if (!store.data || store.data.accepting_orders) return null;
  const Icon = store.data.is_paused ? CirclePause : Clock;
  return (
    <div role="status" className="border-b border-warning/30 bg-warning-soft text-warning">
      <div className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-2.5 text-sm font-medium sm:px-6">
        <Icon className="size-4 shrink-0" aria-hidden />
        <span>
          {store.data.message} Você pode montar o carrinho e finalizar quando a loja voltar a receber
          pedidos.
        </span>
      </div>
    </div>
  );
}
