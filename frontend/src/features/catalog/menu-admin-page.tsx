import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CirclePause,
  CirclePlay,
  Ellipsis,
  Pencil,
  Plus,
  Search,
  Trash,
  UtensilsCrossed,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { catalogApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { AvailabilityBadge, EmptyState, ErrorState, PageHeader, TableSkeleton } from "@/components/common";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Field, Input, Select } from "@/components/ui/field";
import { Menu, MenuContent, MenuItem, MenuTrigger } from "@/components/ui/menu";
import { Card, Table, TD, TH, THead, TR } from "@/components/ui/primitives";
import { formatCurrency } from "@/lib/format";
import type { MenuItem as MenuItemType } from "@/types/api";

/** Itens do cardápio. `readOnly` = consulta da cozinha (receitas e disponibilidade). */
export function MenuAdminPage({ readOnly = false }: { readOnly?: boolean }) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [toDelete, setToDelete] = useState<MenuItemType | null>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const menu = useQuery({ queryKey: queryKeys.menu(), queryFn: () => catalogApi.menu() });
  const categories = useQuery({ queryKey: queryKeys.categories, queryFn: catalogApi.categories, staleTime: Infinity });

  const togglePause = useMutation({
    mutationFn: (item: MenuItemType) => catalogApi.setPaused(item.id, !item.is_paused),
    onSuccess: (item) => {
      toast.success(
        item.is_paused
          ? `${item.name} saiu de venda. O estoque não foi alterado.`
          : `${item.name} voltou a ser vendido.`,
      );
      queryClient.invalidateQueries({ queryKey: queryKeys.menuAll });
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => catalogApi.remove(id),
    onSuccess: () => {
      toast.success("Item excluído do cardápio. Os pedidos antigos continuam no histórico.");
      queryClient.invalidateQueries({ queryKey: queryKeys.menuAll });
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const items = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (menu.data ?? []).filter(
      (i) =>
        (!category || i.category.id === Number(category)) &&
        (!term || i.name.toLowerCase().includes(term) || i.description?.toLowerCase().includes(term)),
    );
  }, [menu.data, search, category]);

  return (
    <div>
      <PageHeader
        title={readOnly ? "Cardápio e receitas" : "Cardápio"}
        description={
          readOnly
            ? "Consulte as receitas e quantas unidades o estoque atual permite preparar."
            : "Itens, preços e receitas. O estoque é descontado conforme a receita a cada pedido."
        }
        actions={
          !readOnly && (
            <Button asChild>
              <Link to="/painel/cardapio/novo">
                <Plus /> Novo item
              </Link>
            </Button>
          )
        }
      />
      <Card>
        <div className="flex flex-wrap items-end gap-3 border-b p-4">
          <Field label="Buscar" className="w-full sm:w-64">
            <div className="relative">
              <Search className="pointer-events-none absolute top-2.5 left-3 size-4 text-muted-foreground" aria-hidden />
              <Input className="pl-9" placeholder="Nome ou descrição" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </Field>
          <Field label="Categoria" className="w-full sm:w-48">
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Todas</option>
              {categories.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        {menu.isPending ? (
          <TableSkeleton rows={6} columns={5} />
        ) : menu.isError ? (
          <ErrorState error={menu.error} onRetry={() => menu.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={UtensilsCrossed}
            title={menu.data.length === 0 ? "Nenhum item no cardápio" : "Nenhum item encontrado"}
            description={
              menu.data.length === 0 && !readOnly
                ? "Cadastre o primeiro item com sua receita para começar a vender."
                : "Ajuste a busca ou a categoria."
            }
            action={
              menu.data.length === 0 && !readOnly ? (
                <Button asChild>
                  <Link to="/painel/cardapio/novo">
                    <Plus /> Novo item
                  </Link>
                </Button>
              ) : undefined
            }
          />
        ) : (
          <Table>
            <THead>
              <tr>
                <TH>Item</TH>
                <TH className="hidden md:table-cell">Categoria</TH>
                <TH className="hidden lg:table-cell">Receita (por unidade)</TH>
                <TH className="text-right">Preço</TH>
                <TH>Disponibilidade</TH>
                {!readOnly && (
                  <TH className="w-12">
                    <span className="sr-only">Ações</span>
                  </TH>
                )}
              </tr>
            </THead>
            <tbody>
              {items.map((item) => (
                <TR key={item.id}>
                  <TD>
                    <div className="flex items-center gap-3">
                      <div className="size-11 shrink-0 overflow-hidden rounded-md bg-muted">
                        {item.image_url ? (
                          <img src={item.image_url} alt="" className="size-full object-cover" loading="lazy" />
                        ) : (
                          <UtensilsCrossed className="m-3 size-5 text-muted-foreground" aria-hidden />
                        )}
                      </div>
                      <div className="min-w-0">
                        {readOnly ? (
                          <p className="font-medium">{item.name}</p>
                        ) : (
                          <Link to={`/painel/cardapio/${item.id}`} className="font-medium hover:underline">
                            {item.name}
                          </Link>
                        )}
                        {item.description && (
                          <p className="line-clamp-1 max-w-xs text-xs text-muted-foreground">{item.description}</p>
                        )}
                      </div>
                    </div>
                  </TD>
                  <TD className="hidden md:table-cell">{item.category.name}</TD>
                  <TD className="hidden text-muted-foreground lg:table-cell">
                    {item.recipe && item.recipe.length > 0
                      ? item.recipe.map((r) => `${r.quantity}× ${r.ingredient_name}`).join(", ")
                      : "Sem receita (não usa o estoque)"}
                  </TD>
                  <TD className="tabular text-right font-medium">{formatCurrency(item.price)}</TD>
                  <TD>
                    <AvailabilityBadge availability={item.availability} portions={item.portions} />
                    {item.portions !== null && item.availability === "available" && (
                      <span className="tabular ml-2 text-xs text-muted-foreground">{item.portions} un.</span>
                    )}
                  </TD>
                  {!readOnly && (
                    <TD>
                      <Menu>
                        <MenuTrigger asChild>
                          <Button variant="ghost" size="icon-sm" aria-label={`Ações de ${item.name}`}>
                            <Ellipsis />
                          </Button>
                        </MenuTrigger>
                        <MenuContent>
                          <MenuItem onSelect={() => navigate(`/painel/cardapio/${item.id}`)}>
                            <Pencil /> Editar
                          </MenuItem>
                          <MenuItem onSelect={() => togglePause.mutate(item)}>
                            {item.is_paused ? <CirclePlay /> : <CirclePause />}
                            {item.is_paused ? "Voltar a vender" : "Pausar venda"}
                          </MenuItem>
                          <MenuItem destructive onSelect={() => setToDelete(item)}>
                            <Trash /> Excluir
                          </MenuItem>
                        </MenuContent>
                      </Menu>
                    </TD>
                  )}
                </TR>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {toDelete && (
        <ConfirmDialog
          open
          onOpenChange={(open) => !open && setToDelete(null)}
          title={`Excluir "${toDelete.name}"?`}
          description="O item e a receita saem do cardápio. Pedidos já feitos continuam no histórico com o nome e o preço da época."
          confirmLabel="Excluir item"
          destructive
          onConfirm={() => remove.mutateAsync(toDelete.id)}
        />
      )}
    </div>
  );
}
