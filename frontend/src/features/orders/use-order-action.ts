import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import type { OrderAction } from "@/types/api";

export function useOrderAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action, reason }: { id: number; action: OrderAction; reason?: string | null }) =>
      ordersApi.act(id, action, reason),
    onSuccess: (result) => {
      toast.success(result.message);
      queryClient.setQueryData(queryKeys.order(result.order.id), result.order);
    },
    onError: (error) => toast.error(errorMessage(error)),
    // Sucesso ou conflito (outra pessoa já mudou o pedido): atualiza listas e contadores.
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ordersAll });
      queryClient.invalidateQueries({ queryKey: queryKeys.menuAll });
      queryClient.invalidateQueries({ queryKey: queryKeys.inventoryAll });
    },
  });
}
