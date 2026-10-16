import { useQuery } from "@tanstack/react-query";
import { Plus, UtensilsCrossed } from "lucide-react";
import { useMemo } from "react";
import { Navigate, useOutletContext, useSearchParams } from "react-router";
import { toast } from "sonner";

import { catalogApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import type { StorefrontContext } from "@/app/layouts";
import { AvailabilityBadge, EmptyState, ErrorState, QuantityStepper } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/primitives";
import { HOME_BY_ROLE, useSession } from "@/features/auth/session";
import { MAX_ITEM_QUANTITY, useCart } from "@/features/cart/store";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Category, MenuItem } from "@/types/api";

export function MenuPage() {
  const session = useSession();
  const [params, setParams] = useSearchParams();
  const selected = Number(params.get("categoria")) || null;

  const categories = useQuery({ queryKey: queryKeys.categories, queryFn: catalogApi.categories, staleTime: Infinity });
  const menu = useQuery({ queryKey: queryKeys.menu(), queryFn: () => catalogApi.menu() });

  const sections = useMemo(() => {
    const items = menu.data ?? [];
    return (categories.data ?? [])
      .filter((c) => selected === null || c.id === selected)
      .map((category) => ({ category, items: items.filter((i) => i.category.id === category.id) }))
      .filter((s) => s.items.length > 0);
  }, [menu.data, categories.data, selected]);

  // Como no sistema original, a equipe é levada direto para a sua área.
  if (session.data && session.data.role !== "customer") {
    return <Navigate to={HOME_BY_ROLE[session.data.role]} replace />;
  }

  const selectCategory = (id: number | null) =>
    setParams(id ? { categoria: String(id) } : {}, { replace: true, preventScrollReset: true });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold tracking-tight">Cardápio</h1>
        <p className="mt-1 text-muted-foreground">
          Hambúrgueres artesanais, acompanhamentos e bebidas — feitos na hora.
        </p>
      </div>

      <CategoryChips categories={categories.data} selected={selected} onSelect={selectCategory} />

      {menu.isPending || categories.isPending ? (
        <MenuSkeleton />
      ) : menu.isError ? (
        <ErrorState error={menu.error} onRetry={() => menu.refetch()} />
      ) : sections.length === 0 ? (
        <EmptyState
          icon={UtensilsCrossed}
          title="Nenhum item nesta categoria"
          description="Escolha outra categoria para ver mais opções."
          action={<Button variant="outline" onClick={() => selectCategory(null)}>Ver todo o cardápio</Button>}
        />
      ) : (
        <div className="flex flex-col gap-10">
          {sections.map(({ category, items }) => (
            <section key={category.id} aria-labelledby={`categoria-${category.id}`}>
              <h2 id={`categoria-${category.id}`} className="mb-4 text-lg font-semibold">
                {category.name}
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((item) => (
                  <ProductCard key={item.id} item={item} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

function CategoryChips({
  categories,
  selected,
  onSelect,
}: {
  categories: Category[] | undefined;
  selected: number | null;
  onSelect: (id: number | null) => void;
}) {
  const options = [{ id: null, name: "Todos" }, ...(categories ?? [])];
  return (
    <div className="sticky top-16 z-30 -mx-4 mb-6 border-b bg-background/90 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
      <div className="flex gap-2 overflow-x-auto" role="toolbar" aria-label="Filtrar por categoria">
        {options.map((option) => {
          const active = option.id === selected;
          return (
            <button
              key={option.id ?? "todos"}
              type="button"
              onClick={() => onSelect(option.id)}
              aria-pressed={active}
              className={cn(
                "h-9 shrink-0 rounded-full border px-4 text-sm font-medium transition-colors",
                active
                  ? "border-foreground bg-foreground text-background"
                  : "border-border bg-surface text-muted-foreground hover:border-input hover:text-foreground",
              )}
            >
              {option.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ProductCard({ item }: { item: MenuItem }) {
  const { openCart } = useOutletContext<StorefrontContext>();
  const inCart = useCart((s) => s.lines.find((l) => l.menuItemId === item.id)?.quantity ?? 0);
  const add = useCart((s) => s.add);
  const setQuantity = useCart((s) => s.setQuantity);
  const soldOut = item.availability === "sold_out";
  // Como no original: não deixa pedir mais do que o estoque permite fazer.
  const max = Math.min(MAX_ITEM_QUANTITY, item.portions ?? MAX_ITEM_QUANTITY);

  function handleAdd() {
    add(item, 1);
    toast.success(`${item.name} adicionado ao carrinho`, {
      action: { label: "Ver carrinho", onClick: openCart },
    });
  }

  return (
    <article
      className={cn(
        "group flex flex-col overflow-hidden rounded-lg border bg-surface shadow-xs transition-shadow hover:shadow-md",
        soldOut && "opacity-70",
      )}
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        {item.image_url ? (
          <img
            src={item.image_url}
            alt={item.name}
            loading="lazy"
            className="size-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          />
        ) : (
          <div className="flex size-full items-center justify-center">
            <UtensilsCrossed className="size-8 text-muted-foreground/60" aria-hidden />
          </div>
        )}
        {item.availability !== "available" && (
          <div className="absolute top-3 left-3">
            <AvailabilityBadge availability={item.availability} portions={item.portions} />
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <h3 className="font-semibold">{item.name}</h3>
        {item.description && (
          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{item.description}</p>
        )}
        <div className="mt-auto flex items-center justify-between gap-3 pt-4">
          <span className="tabular text-base font-semibold">{formatCurrency(item.price)}</span>
          {soldOut ? (
            <Button variant="secondary" disabled>
              Esgotado
            </Button>
          ) : inCart > 0 ? (
            <QuantityStepper
              value={inCart}
              min={0}
              max={max}
              label={`quantidade de ${item.name} no carrinho`}
              onChange={(q) => setQuantity(item.id, q)}
            />
          ) : (
            <Button onClick={handleAdd} aria-label={`Adicionar ${item.name} ao carrinho`}>
              <Plus /> Adicionar
            </Button>
          )}
        </div>
      </div>
    </article>
  );
}

function MenuSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-label="Carregando cardápio">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="overflow-hidden rounded-lg border bg-surface">
          <Skeleton className="aspect-[4/3] rounded-none" />
          <div className="space-y-2 p-4">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="mt-4 h-9 w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
