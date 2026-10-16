import type { OrderFilters } from "@/types/api";

// Chaves do cache do TanStack Query. Invalidar um prefixo (ex.: ["orders"]) atualiza
// todas as listas e detalhes relacionados.
export const queryKeys = {
  session: ["session"] as const,
  profile: ["profile"] as const,
  categories: ["categories"] as const,
  menu: (categoryId?: number) => ["menu", { categoryId: categoryId ?? null }] as const,
  menuAll: ["menu"] as const,
  menuItem: (id: number) => ["menu", "item", id] as const,
  inventory: (q?: string) => ["inventory", { q: q ?? "" }] as const,
  inventoryAll: ["inventory"] as const,
  orders: (filters: OrderFilters) => ["orders", "list", filters] as const,
  ordersAll: ["orders"] as const,
  order: (id: number) => ["orders", "detail", id] as const,
  ordersSummary: ["orders", "summary"] as const,
  report: (start?: string, end?: string) => ["report", { start, end }] as const,
  staff: ["staff"] as const,
};
