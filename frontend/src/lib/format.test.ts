import { describe, expect, it } from "vitest";

import { formatCpf, formatCurrency, formatDate, formatDateTime, formatRelative } from "@/lib/format";

describe("formatDate", () => {
  it("mantém o dia de datas sem hora, mesmo em fuso negativo", () => {
    // Os testes rodam em America/Sao_Paulo (UTC-3), onde o deslocamento apareceria.
    expect(new Date("2026-03-01T00:00:00Z").getDate()).toBe(28);
    expect(formatDate("2026-03-01")).toBe("01/03/2026");
    expect(formatDate("2026-03-01", "day-month")).toBe("01/03");
    expect(formatDate("2026-03-01", "long")).toBe("1 de março de 2026");
  });
});

describe("formatDateTime", () => {
  it("exibe o horário no fuso da lanchonete", () => {
    expect(formatDateTime("2026-03-01T02:30:00Z")).toBe("28/02/2026, 23:30");
  });
});

describe("formatCurrency", () => {
  it("usa real com vírgula decimal e ponto de milhar", () => {
    // O Intl separa "R$" do valor com espaço não separável.
    expect(formatCurrency("12.5")).toBe("R$ 12,50");
    expect(formatCurrency(1234.56)).toBe("R$ 1.234,56");
    expect(formatCurrency("0")).toBe("R$ 0,00");
  });
});

describe("formatRelative", () => {
  const now = Date.parse("2026-03-10T12:00:00Z");
  const ago = (minutes: number) => new Date(now - minutes * 60_000).toISOString();

  it("escolhe a unidade pelo tempo decorrido", () => {
    expect(formatRelative(ago(0), now)).toBe("agora");
    expect(formatRelative(ago(5), now)).toBe("há 5 min");
    expect(formatRelative(ago(150), now)).toBe("há 2 h");
    expect(formatRelative(ago(24 * 60), now)).toBe("ontem");
    expect(formatRelative(ago(3 * 24 * 60), now)).toBe("há 3 dias");
  });
});

describe("formatCpf", () => {
  it("aplica a máscara aos poucos e ignora o que não é dígito", () => {
    expect(formatCpf("529")).toBe("529");
    expect(formatCpf("5299")).toBe("529.9");
    expect(formatCpf("5299822")).toBe("529.982.2");
    expect(formatCpf("52998224725999")).toBe("529.982.247-25");
    expect(formatCpf("529.982.247-25")).toBe("529.982.247-25");
  });
});
