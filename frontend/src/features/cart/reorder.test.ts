import { describe, expect, it } from "vitest";

import { planReorder } from "@/features/cart/reorder";
import { menuItem, order as makeOrder } from "@/test/factories";
import type { Order, OrderItem } from "@/types/api";

function line(overrides: Partial<OrderItem>): OrderItem {
  return {
    id: 1,
    menu_item_id: 1,
    product_name: "Cali Clássico",
    unit_price: "22.00",
    quantity: 1,
    subtotal: "22.00",
    notes: null,
    ...overrides,
  };
}

function order(items: OrderItem[]): Order {
  return makeOrder({ id: 7, status: "completed", items });
}

describe("planReorder", () => {
  it("usa o cardápio atual e mantém as observações", () => {
    const menu = [menuItem({ id: 1, name: "Cali Clássico", price: "24.00" })];
    const plan = planReorder(order([line({ quantity: 2, notes: "sem cebola" })]), menu);
    expect(plan.lines).toEqual([{ item: menu[0], quantity: 2, notes: "sem cebola" }]);
    expect(plan.skipped).toEqual([]);
  });

  it("deixa de fora o que saiu do cardápio, esgotou ou foi pausado", () => {
    const menu = [
      menuItem({ id: 2, name: "Cali Duplo", availability: "sold_out", portions: 0 }),
      menuItem({ id: 3, name: "Suco", availability: "paused", is_paused: true }),
    ];
    const plan = planReorder(
      order([
        line({ menu_item_id: null, product_name: "Item antigo" }),
        line({ menu_item_id: 2, product_name: "Cali Duplo" }),
        line({ menu_item_id: 3, product_name: "Suco" }),
      ]),
      menu,
    );
    expect(plan.lines).toEqual([]);
    expect(plan.skipped).toEqual(["Item antigo", "Cali Duplo", "Suco"]);
  });

  it("reduz a quantidade ao estoque e ao que já está no carrinho", () => {
    const menu = [menuItem({ id: 1, name: "Cali Clássico", portions: 3, availability: "low" })];
    const reduced = planReorder(order([line({ quantity: 5 })]), menu);
    expect(reduced.lines[0]?.quantity).toBe(3);
    expect(reduced.reduced).toEqual(["Cali Clássico"]);

    const full = planReorder(order([line({ quantity: 1 })]), menu, { 1: 3 });
    expect(full.lines).toEqual([]);
    expect(full.skipped).toEqual(["Cali Clássico"]);
  });

  it("respeita o limite de 20 por item", () => {
    const menu = [menuItem({ id: 1, portions: null })];
    expect(planReorder(order([line({ quantity: 20 })]), menu, { 1: 15 }).lines[0]?.quantity).toBe(5);
  });
});
