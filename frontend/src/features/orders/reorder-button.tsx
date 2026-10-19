import { RotateCcw } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";

import { Button, type ButtonProps } from "@/components/ui/button";
import { useReorder } from "@/features/cart/reorder";
import type { Order } from "@/types/api";

/** "Pedir de novo": coloca os itens no carrinho e leva à revisão do pedido. */
export function ReorderButton({ order, size = "sm" }: { order: Order; size?: ButtonProps["size"] }) {
  const reorder = useReorder();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  if (!order.items.some((i) => i.menu_item_id !== null)) return null;

  return (
    <Button
      variant="outline"
      size={size}
      loading={busy}
      onClick={async () => {
        setBusy(true);
        try {
          if (await reorder(order)) navigate("/checkout");
        } finally {
          setBusy(false);
        }
      }}
    >
      {!busy && <RotateCcw />} Pedir de novo
    </Button>
  );
}
