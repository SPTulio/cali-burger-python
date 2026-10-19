import { describe, expect, it } from "vitest";

import { HOME_BY_ROLE, safeNext } from "@/features/auth/session";

describe("safeNext", () => {
  it("aceita caminhos internos da área do papel", () => {
    expect(safeNext("/pedidos/12", "customer")).toBe("/pedidos/12");
    expect(safeNext("/painel/estoque", "manager")).toBe("/painel/estoque");
    expect(safeNext("/cozinha", "cook")).toBe("/cozinha");
  });

  it.each(["//evil.example", "//evil.example/painel", "https://evil.example", "javascript:alert(1)", "pedidos"])(
    "recusa o destino externo %s",
    (next) => {
      expect(safeNext(next, "customer")).toBe(HOME_BY_ROLE.customer);
      expect(safeNext(next, "manager")).toBe(HOME_BY_ROLE.manager);
    },
  );

  it("não manda o cliente para a área da equipe nem a equipe para a loja", () => {
    expect(safeNext("/painel/pedidos", "customer")).toBe("/");
    expect(safeNext("/carrinho", "manager")).toBe("/painel/pedidos");
    expect(safeNext("/carrinho", "cook")).toBe("/cozinha");
  });

  it("sem destino, usa a página inicial do papel", () => {
    expect(safeNext(null, "customer")).toBe("/");
    expect(safeNext("", "cook")).toBe("/cozinha");
  });
});
