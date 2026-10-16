import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MapPin, QrCode, ShieldCheck, ShoppingBag, TriangleAlert } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";

import { ApiError, errorMessage } from "@/api/client";
import { accountApi, catalogApi, ordersApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Field, Input } from "@/components/ui/field";
import { Card, CardHeader, Skeleton } from "@/components/ui/primitives";
import { CartLineRow } from "@/features/cart/cart-sheet";
import { cartTotals, useCart } from "@/features/cart/store";
import { formatCurrency } from "@/lib/format";
import { newIdempotencyKey } from "@/lib/utils";
import { addressSchema, applyApiErrors } from "@/lib/validation";
import type { Address } from "@/types/api";

export function CheckoutPage() {
  const lines = useCart((s) => s.lines);
  const sync = useCart((s) => s.sync);
  const clearCart = useCart((s) => s.clear);
  const { total } = cartTotals(lines);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [addressOpen, setAddressOpen] = useState(false);

  const profile = useQuery({ queryKey: queryKeys.profile, queryFn: accountApi.profile });
  const menu = useQuery({ queryKey: queryKeys.menu(), queryFn: () => catalogApi.menu() });

  // Itens que saíram do cardápio são retirados do carrinho (como no sistema original).
  useEffect(() => {
    if (!menu.data) return;
    const removed = sync(menu.data);
    if (removed.length) {
      toast.warning(`Saiu do cardápio e foi retirado do carrinho: ${removed.join(", ")}.`);
    }
  }, [menu.data, sync]);

  // Uma chave por conteúdo do carrinho: reenvios (duplo clique, rede instável) não duplicam
  // o pedido; mudar o carrinho gera uma nova tentativa.
  const cartSignature = JSON.stringify(lines.map((l) => [l.menuItemId, l.quantity, l.notes]));
  const idempotencyKey = useMemo(() => newIdempotencyKey(), [cartSignature]); // eslint-disable-line react-hooks/exhaustive-deps

  const stockWarnings = useMemo(() => {
    const byId = new Map((menu.data ?? []).map((m) => [m.id, m]));
    return lines
      .filter((l) => {
        const item = byId.get(l.menuItemId);
        return item && item.portions !== null && l.quantity > item.portions;
      })
      .map((l) => {
        const portions = byId.get(l.menuItemId)!.portions!;
        return portions === 0 ? `${l.name} esgotou.` : `${l.name}: restam só ${portions}.`;
      });
  }, [lines, menu.data]);

  const placeOrder = useMutation({
    mutationFn: () =>
      ordersApi.create(
        lines.map((l) => ({ menu_item_id: l.menuItemId, quantity: l.quantity, notes: l.notes.trim() || null })),
        idempotencyKey,
      ),
    onSuccess: (order) => {
      clearCart();
      queryClient.invalidateQueries({ queryKey: queryKeys.ordersAll });
      queryClient.invalidateQueries({ queryKey: queryKeys.menuAll });
      navigate(`/pedidos/${order.id}?novo=1`, { replace: true });
    },
    onError: (error) => {
      if (error instanceof ApiError && error.code === "missing_address") setAddressOpen(true);
      if (error instanceof ApiError && error.status === 409) {
        queryClient.invalidateQueries({ queryKey: queryKeys.menuAll });
      }
      toast.error(errorMessage(error));
    },
  });

  if (lines.length === 0) {
    return (
      <EmptyState
        icon={ShoppingBag}
        title="Seu carrinho está vazio"
        description="Adicione itens do cardápio para finalizar um pedido."
        action={
          <Button asChild>
            <Link to="/">Ver o cardápio</Link>
          </Button>
        }
      />
    );
  }

  const address = profile.data?.address;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Revisar pedido</h1>
      <div className="grid items-start gap-6 lg:grid-cols-[1fr_380px]">
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader
              title="Endereço de entrega"
              actions={
                address && (
                  <Button variant="outline" size="sm" onClick={() => setAddressOpen(true)}>
                    Alterar
                  </Button>
                )
              }
            />
            <div className="flex items-start gap-3 px-5 py-4">
              <MapPin className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
              {profile.isPending ? (
                <Skeleton className="h-4 w-2/3" />
              ) : profile.isError ? (
                <ErrorState error={profile.error} onRetry={() => profile.refetch()} />
              ) : address ? (
                <p className="text-sm">
                  {address.street}, {address.district}
                  <br />
                  <span className="text-muted-foreground">
                    {address.city} - {address.state}
                  </span>
                </p>
              ) : (
                <div className="text-sm">
                  <p>Nenhum endereço cadastrado.</p>
                  <Button variant="link" onClick={() => setAddressOpen(true)}>
                    Cadastrar endereço
                  </Button>
                </div>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Itens" description="Ajuste quantidades e observações antes de pagar." />
            <ul className="divide-y px-5">
              {lines.map((line) => (
                <CartLineRow key={line.menuItemId} line={line} />
              ))}
            </ul>
          </Card>
        </div>

        <Card className="lg:sticky lg:top-24">
          <CardHeader title="Pagamento" description="PIX" />
          <div className="flex flex-col gap-4 px-5 py-4">
            <div className="flex items-center gap-4 rounded-md border border-dashed p-4">
              <div className="flex size-16 shrink-0 items-center justify-center rounded-md bg-muted">
                <QrCode className="size-9 text-foreground" aria-hidden />
              </div>
              <p className="text-xs text-muted-foreground">
                <strong className="text-foreground">Demonstração:</strong> o PIX é simulado e
                nenhum valor é cobrado. Ao confirmar, o pedido é registrado como pago.
              </p>
            </div>
            {stockWarnings.length > 0 && (
              <div role="alert" className="flex gap-2 rounded-md bg-warning-soft p-3 text-sm text-warning">
                <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
                <div>
                  {stockWarnings.map((w) => (
                    <p key={w}>{w}</p>
                  ))}
                </div>
              </div>
            )}
            <dl className="flex flex-col gap-2 text-sm">
              <div className="flex justify-between text-muted-foreground">
                <dt>Subtotal</dt>
                <dd className="tabular">{formatCurrency(total)}</dd>
              </div>
              <div className="flex justify-between border-t pt-3 text-base font-semibold">
                <dt>Total</dt>
                <dd className="tabular">{formatCurrency(total)}</dd>
              </div>
            </dl>
            <Button
              size="lg"
              onClick={() => placeOrder.mutate()}
              loading={placeOrder.isPending}
              disabled={!address || stockWarnings.length > 0}
            >
              <ShieldCheck /> Confirmar pagamento
            </Button>
            <Button asChild variant="ghost">
              <Link to="/">Continuar comprando</Link>
            </Button>
          </div>
        </Card>
      </div>

      <AddressDialog open={addressOpen} onOpenChange={setAddressOpen} initial={address ?? null} />
    </div>
  );
}

export function AddressDialog({
  open,
  onOpenChange,
  initial,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initial: Address | null;
}) {
  const queryClient = useQueryClient();
  const form = useForm<Address>({
    resolver: zodResolver(addressSchema),
    values: initial ?? { street: "", district: "", city: "", state: "" },
  });
  const { errors } = form.formState;
  const save = useMutation({
    mutationFn: accountApi.updateAddress,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile });
      toast.success("Endereço atualizado.");
      onOpenChange(false);
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader title="Endereço de entrega" description="Usado nos próximos pedidos." />
        <form
          id="address-form"
          className="grid gap-4 sm:grid-cols-2"
          onSubmit={form.handleSubmit((data) => save.mutate(data))}
          noValidate
        >
          <Field label="Logradouro" error={errors.street?.message} className="sm:col-span-2">
            <Input placeholder="Rua, número e complemento" autoComplete="street-address" {...form.register("street")} />
          </Field>
          <Field label="Bairro" error={errors.district?.message}>
            <Input {...form.register("district")} />
          </Field>
          <Field label="Cidade" error={errors.city?.message}>
            <Input autoComplete="address-level2" {...form.register("city")} />
          </Field>
          <Field label="Estado" error={errors.state?.message}>
            <Input autoComplete="address-level1" {...form.register("state")} />
          </Field>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit" form="address-form" loading={save.isPending}>
            Salvar endereço
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
