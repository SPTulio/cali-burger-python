import { beforeEach, describe, expect, it } from "vitest";

import {
  cartTotals,
  MAX_ITEM_QUANTITY,
  MAX_NOTES_LENGTH,
  useCart,
  type CartLine,
} from "@/features/cart/store";
import { menuItem } from "@/test/factories";

const burger = menuItem({ id: 1, name: "Cali Clássico", price: "29.90" });
const fries = menuItem({ id: 2, name: "Batata Frita", price: "12.50" });

const lines = () => useCart.getState().lines;

beforeEach(() => {
  useCart.setState({ lines: [] });
});

describe("useCart.add", () => {
  it("cria a linha com os dados do cardápio", () => {
    expect(useCart.getState().add(burger, 2)).toBe(2);
    expect(lines()).toEqual([
      { menuItemId: 1, name: "Cali Clássico", price: "29.90", imageUrl: null, quantity: 2, notes: "" },
    ]);
  });

  it("soma à linha existente em vez de duplicar o item", () => {
    useCart.getState().add(burger);
    useCart.getState().add(fries);
    useCart.getState().add(burger, 3);
    expect(lines().map((l) => [l.menuItemId, l.quantity])).toEqual([
      [1, 4],
      [2, 1],
    ]);
  });

  it(`não passa de ${MAX_ITEM_QUANTITY} por item e devolve só o que entrou`, () => {
    useCart.getState().add(burger, 18);
    expect(useCart.getState().add(burger, 5)).toBe(2);
    expect(lines()[0]?.quantity).toBe(MAX_ITEM_QUANTITY);
    expect(useCart.getState().add(burger)).toBe(0);
    expect(lines()[0]?.quantity).toBe(MAX_ITEM_QUANTITY);
  });
});

describe("useCart.setQuantity e setNotes", () => {
  it("limita a quantidade e remove a linha ao chegar a zero", () => {
    useCart.getState().add(burger);
    useCart.getState().setQuantity(1, 99);
    expect(lines()[0]?.quantity).toBe(MAX_ITEM_QUANTITY);
    useCart.getState().setQuantity(1, 0);
    expect(lines()).toEqual([]);
  });

  it("corta a observação no tamanho aceito pelo servidor", () => {
    useCart.getState().add(burger);
    useCart.getState().setNotes(1, "x".repeat(MAX_NOTES_LENGTH + 10));
    expect(lines()[0]?.notes).toHaveLength(MAX_NOTES_LENGTH);
  });
});

describe("useCart.sync", () => {
  it("remove o que saiu do cardápio e atualiza nome, preço e foto do resto", () => {
    useCart.getState().add(burger, 2);
    useCart.getState().add(fries);
    useCart.getState().setNotes(1, "sem cebola");

    const removed = useCart
      .getState()
      .sync([menuItem({ id: 1, name: "Cali Duplo", price: "34.90", image_url: "/media/a.jpg" })]);

    expect(removed).toEqual(["Batata Frita"]);
    expect(lines()).toEqual([
      {
        menuItemId: 1,
        name: "Cali Duplo",
        price: "34.90",
        imageUrl: "/media/a.jpg",
        quantity: 2,
        notes: "sem cebola",
      },
    ]);
  });

  it("não troca o estado quando nada mudou", () => {
    useCart.getState().add(burger);
    const before = lines();
    expect(useCart.getState().sync([burger, fries])).toEqual([]);
    expect(lines()).toBe(before);
  });
});

describe("cartTotals", () => {
  const line = (menuItemId: number, price: string, quantity: number): CartLine => ({
    menuItemId,
    name: "Item",
    price,
    imageUrl: null,
    quantity,
    notes: "",
  });

  it("soma em centavos, sem erro de ponto flutuante", () => {
    // Em float, 0.1 * 3 + 0.2 * 3 daria 0.9000000000000001.
    expect(cartTotals([line(1, "0.10", 3), line(2, "0.20", 3)])).toEqual({ total: 0.9, count: 6 });
    expect(cartTotals([line(1, "29.90", 3), line(2, "12.50", 1)])).toEqual({ total: 102.2, count: 4 });
  });

  it("carrinho vazio", () => {
    expect(cartTotals([])).toEqual({ total: 0, count: 0 });
  });
});
