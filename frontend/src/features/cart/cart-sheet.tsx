import { MessageSquarePlus, ShoppingBag, Trash, UtensilsCrossed } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";

import { EmptyState, QuantityStepper } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, SheetContent } from "@/components/ui/dialog";
import { Input } from "@/components/ui/field";
import { useSession } from "@/features/auth/session";
import { cartTotals, MAX_ITEM_QUANTITY, MAX_NOTES_LENGTH, useCart, type CartLine } from "@/features/cart/store";
import { formatCurrency } from "@/lib/format";

export function CartSheet({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const lines = useCart((s) => s.lines);
  const { total, count } = cartTotals(lines);
  const session = useSession();
  const navigate = useNavigate();

  function checkout() {
    onOpenChange(false);
    navigate(session.data ? "/checkout" : "/entrar?next=%2Fcheckout");
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <SheetContent title="Seu carrinho">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div>
            <h2 className="text-base font-semibold">Seu carrinho</h2>
            <p className="text-sm text-muted-foreground">
              {count === 0 ? "Nenhum item" : `${count} ${count === 1 ? "item" : "itens"}`}
            </p>
          </div>
          <DialogClose asChild>
            <Button variant="ghost" size="sm">
              Fechar
            </Button>
          </DialogClose>
        </div>

        {lines.length === 0 ? (
          <EmptyState
            className="flex-1"
            icon={ShoppingBag}
            title="Seu carrinho está vazio"
            description="Escolha seus lanches no cardápio e eles aparecem aqui."
            action={
              <DialogClose asChild>
                <Button variant="outline">
                  <UtensilsCrossed /> Ver o cardápio
                </Button>
              </DialogClose>
            }
          />
        ) : (
          <>
            <ul className="flex-1 divide-y overflow-y-auto px-5">
              {lines.map((line) => (
                <CartLineRow key={line.menuItemId} line={line} />
              ))}
            </ul>
            <div className="border-t bg-muted/40 px-5 py-4">
              <div className="mb-3 flex items-center justify-between text-base font-semibold">
                <span>Total</span>
                <span className="tabular">{formatCurrency(total)}</span>
              </div>
              <Button size="lg" className="w-full" onClick={checkout}>
                Revisar e pagar
              </Button>
              {!session.data && (
                <p className="mt-2 text-center text-xs text-muted-foreground">
                  Você vai entrar na sua conta antes de pagar.
                </p>
              )}
            </div>
          </>
        )}
      </SheetContent>
    </Dialog>
  );
}

export function CartLineRow({ line }: { line: CartLine }) {
  const setQuantity = useCart((s) => s.setQuantity);
  const setNotes = useCart((s) => s.setNotes);
  const remove = useCart((s) => s.remove);
  const [showNotes, setShowNotes] = useState(Boolean(line.notes));

  return (
    <li className="flex gap-3 py-4">
      <div className="size-16 shrink-0 overflow-hidden rounded-md bg-muted">
        {line.imageUrl ? (
          <img src={line.imageUrl} alt="" className="size-full object-cover" />
        ) : (
          <UtensilsCrossed className="m-auto mt-5 size-5 text-muted-foreground" aria-hidden />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate font-medium">{line.name}</p>
            <p className="tabular text-sm text-muted-foreground">{formatCurrency(line.price)} cada</p>
          </div>
          <p className="tabular font-medium">
            {formatCurrency((Math.round(Number(line.price) * 100) * line.quantity) / 100)}
          </p>
        </div>
        <div className="mt-2 flex items-center justify-between gap-2">
          <QuantityStepper
            size="sm"
            value={line.quantity}
            min={1}
            max={MAX_ITEM_QUANTITY}
            label={`quantidade de ${line.name}`}
            onChange={(q) => setQuantity(line.menuItemId, q)}
          />
          <div className="flex items-center">
            {!showNotes && (
              <Button variant="ghost" size="sm" onClick={() => setShowNotes(true)}>
                <MessageSquarePlus /> Observação
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => remove(line.menuItemId)}
              aria-label={`Remover ${line.name}`}
            >
              <Trash className="text-muted-foreground" />
            </Button>
          </div>
        </div>
        {showNotes && (
          <Input
            className="mt-2 h-8 text-[13px]"
            placeholder="Ex.: sem cebola"
            maxLength={MAX_NOTES_LENGTH}
            value={line.notes}
            onChange={(e) => setNotes(line.menuItemId, e.target.value)}
            aria-label={`Observação para ${line.name}`}
            autoFocus={!line.notes}
          />
        )}
      </div>
    </li>
  );
}
