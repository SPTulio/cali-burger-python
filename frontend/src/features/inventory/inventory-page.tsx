import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ellipsis, Package, PackageOpen, Pencil, Plus, Search, Trash, TriangleAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { errorMessage } from "@/api/client";
import { inventoryApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState, PageHeader, StatCard, StockBadge, TableSkeleton } from "@/components/common";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog, DialogContent, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Field, Input, Select } from "@/components/ui/field";
import { Menu, MenuContent, MenuItem, MenuTrigger } from "@/components/ui/menu";
import { Card, CardHeader, Table, TD, TH, THead, TR } from "@/components/ui/primitives";
import { formatRelative, plural } from "@/lib/format";
import { applyApiErrors, fields } from "@/lib/validation";
import type { Ingredient, StockLevel } from "@/types/api";

const quantity = (min: number) =>
  z.coerce
    .number<string>({ error: "Informe a quantidade." })
    .int("Use um número inteiro.")
    .min(min, `Informe uma quantidade entre ${min} e 100.000.`)
    .max(100_000, `Informe uma quantidade entre ${min} e 100.000.`);

const addSchema = z.object({ name: fields.required(50), quantity: quantity(1) });
const editSchema = z.object({ name: fields.required(50), quantity: quantity(0) });
type FormInput = { name: string; quantity: string };

function useInvalidateStock() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.inventoryAll });
    // A disponibilidade do cardápio depende do estoque.
    queryClient.invalidateQueries({ queryKey: queryKeys.menuAll });
  };
}

export function InventoryPage() {
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState<StockLevel | "">("");
  const [editing, setEditing] = useState<Ingredient | null>(null);
  const [deleting, setDeleting] = useState<Ingredient | null>(null);
  const invalidate = useInvalidateStock();

  const inventory = useQuery({ queryKey: queryKeys.inventory(), queryFn: () => inventoryApi.list() });
  const items = useMemo(() => inventory.data?.items ?? [], [inventory.data]);
  const threshold = inventory.data?.low_stock_threshold ?? 10;
  const low = items.filter((i) => i.level === "low").length;
  const out = items.filter((i) => i.level === "out").length;

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return items.filter((i) => (!level || i.level === level) && (!term || i.name.toLowerCase().includes(term)));
  }, [items, search, level]);

  const remove = useMutation({
    mutationFn: (id: number) => inventoryApi.remove(id),
    onSuccess: () => {
      toast.success("Ingrediente excluído.");
      invalidate();
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  return (
    <div>
      <PageHeader title="Estoque" description="Ingredientes usados nas receitas do cardápio." />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard label="Ingredientes" value={items.length} icon={Package} />
        <StatCard label="Estoque baixo" value={low} hint={`${threshold} unidades ou menos`} icon={TriangleAlert} />
        <StatCard label="Em falta" value={out} hint="Itens que usam ficam esgotados" icon={PackageOpen} />
      </div>

      <AddStockCard existing={items} />

      <Card className="mt-6">
        <div className="flex flex-wrap items-end gap-3 border-b p-4">
          <Field label="Buscar" className="w-full sm:w-64">
            <div className="relative">
              <Search className="pointer-events-none absolute top-2.5 left-3 size-4 text-muted-foreground" aria-hidden />
              <Input className="pl-9" placeholder="Nome do ingrediente" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </Field>
          <Field label="Situação" className="w-full sm:w-48">
            <Select value={level} onChange={(e) => setLevel(e.target.value as StockLevel | "")}>
              <option value="">Todas</option>
              <option value="ok">OK</option>
              <option value="low">Estoque baixo</option>
              <option value="out">Em falta</option>
            </Select>
          </Field>
        </div>
        {inventory.isPending ? (
          <TableSkeleton rows={6} columns={4} />
        ) : inventory.isError ? (
          <ErrorState error={inventory.error} onRetry={() => inventory.refetch()} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Package}
            title={items.length === 0 ? "Nenhum ingrediente cadastrado" : "Nenhum ingrediente encontrado"}
            description={items.length === 0 ? "Adicione ingredientes acima para montar as receitas do cardápio." : "Ajuste a busca ou o filtro."}
          />
        ) : (
          <Table>
            <THead>
              <tr>
                <TH>Ingrediente</TH>
                <TH className="text-right">Em estoque</TH>
                <TH className="hidden sm:table-cell">Usado em</TH>
                <TH>Situação</TH>
                <TH className="hidden md:table-cell">Atualizado</TH>
                <TH className="w-12">
                  <span className="sr-only">Ações</span>
                </TH>
              </tr>
            </THead>
            <tbody>
              {filtered.map((ingredient) => (
                <TR key={ingredient.id}>
                  <TD className="font-medium">{ingredient.name}</TD>
                  <TD className="tabular text-right font-medium">{ingredient.quantity.toLocaleString("pt-BR")}</TD>
                  <TD className="hidden text-muted-foreground sm:table-cell">
                    {ingredient.used_in ? plural(ingredient.used_in, "item", "itens") : "Nenhum item"}
                  </TD>
                  <TD>
                    <StockBadge level={ingredient.level} />
                  </TD>
                  <TD className="hidden text-muted-foreground md:table-cell">{formatRelative(ingredient.updated_at)}</TD>
                  <TD>
                    <Menu>
                      <MenuTrigger asChild>
                        <Button variant="ghost" size="icon-sm" aria-label={`Ações de ${ingredient.name}`}>
                          <Ellipsis />
                        </Button>
                      </MenuTrigger>
                      <MenuContent>
                        <MenuItem onSelect={() => setEditing(ingredient)}>
                          <Pencil /> Editar
                        </MenuItem>
                        <MenuItem destructive onSelect={() => setDeleting(ingredient)}>
                          <Trash /> Excluir
                        </MenuItem>
                      </MenuContent>
                    </Menu>
                  </TD>
                </TR>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {editing && <EditDialog ingredient={editing} onClose={() => setEditing(null)} />}
      {deleting && (
        <ConfirmDialog
          open
          onOpenChange={(open) => !open && setDeleting(null)}
          title={`Excluir "${deleting.name}"?`}
          description={
            deleting.used_in > 0
              ? `Ele será retirado da receita de ${plural(deleting.used_in, "item", "itens")} do cardápio. Esta ação não pode ser desfeita.`
              : "Esta ação não pode ser desfeita."
          }
          confirmLabel="Excluir ingrediente"
          destructive
          onConfirm={() => remove.mutateAsync(deleting.id)}
        />
      )}
    </div>
  );
}

function AddStockCard({ existing }: { existing: Ingredient[] }) {
  const invalidate = useInvalidateStock();
  const form = useForm<FormInput, unknown, z.output<typeof addSchema>>({
    resolver: zodResolver(addSchema),
    defaultValues: { name: "", quantity: "" },
  });
  const { errors } = form.formState;
  const add = useMutation({
    mutationFn: (data: z.output<typeof addSchema>) => inventoryApi.add(data.name, data.quantity),
    onSuccess: (result) => {
      toast.success(
        result.created
          ? `"${result.ingredient.name}" cadastrado com ${result.added} unidade(s).`
          : `Estoque de "${result.ingredient.name}" atualizado: +${result.added} (agora ${result.ingredient.quantity}).`,
      );
      form.reset();
      invalidate();
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });

  return (
    <Card>
      <CardHeader title="Entrada de estoque" description="Se o ingrediente já existir, a quantidade é somada ao estoque atual." />
      <form className="flex flex-wrap items-start gap-3 p-5" onSubmit={form.handleSubmit((d) => add.mutate(d))} noValidate>
        <Field label="Ingrediente" error={errors.name?.message} className="w-full sm:flex-1">
          <Input list="ingredientes-existentes" placeholder="Ex.: Pão Brioche" maxLength={50} {...form.register("name")} />
        </Field>
        <datalist id="ingredientes-existentes">
          {existing.map((i) => (
            <option key={i.id} value={i.name} />
          ))}
        </datalist>
        <Field label="Quantidade" error={errors.quantity?.message} className="w-full sm:w-40">
          <Input type="number" min={1} max={100000} inputMode="numeric" {...form.register("quantity")} />
        </Field>
        <Button type="submit" loading={add.isPending} className="w-full sm:mt-[22px] sm:w-auto">
          <Plus /> Adicionar
        </Button>
      </form>
    </Card>
  );
}

function EditDialog({ ingredient, onClose }: { ingredient: Ingredient; onClose: () => void }) {
  const invalidate = useInvalidateStock();
  const form = useForm<FormInput, unknown, z.output<typeof editSchema>>({
    resolver: zodResolver(editSchema),
    defaultValues: { name: ingredient.name, quantity: String(ingredient.quantity) },
  });
  const { errors } = form.formState;
  const save = useMutation({
    mutationFn: (data: z.output<typeof editSchema>) => inventoryApi.update(ingredient.id, data.name, data.quantity),
    onSuccess: () => {
      toast.success("Ingrediente atualizado.");
      invalidate();
      onClose();
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader title="Editar ingrediente" description="Use para corrigir o nome ou ajustar a contagem do estoque." />
        <form id="edit-ingredient" className="flex flex-col gap-4" onSubmit={form.handleSubmit((d) => save.mutate(d))} noValidate>
          <Field label="Ingrediente" error={errors.name?.message}>
            <Input maxLength={50} {...form.register("name")} />
          </Field>
          <Field label="Quantidade em estoque" error={errors.quantity?.message}>
            <Input type="number" min={0} max={100000} {...form.register("quantity")} />
          </Field>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form="edit-ingredient" loading={save.isPending}>
            Salvar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
