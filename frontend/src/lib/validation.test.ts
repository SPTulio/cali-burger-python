import type { UseFormRegisterReturn } from "react-hook-form";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/api/client";
import { applyApiErrors, isValidCpf, withCpfMask } from "@/lib/validation";

describe("isValidCpf", () => {
  it("aceita CPF válido com ou sem máscara", () => {
    expect(isValidCpf("529.982.247-25")).toBe(true);
    expect(isValidCpf("52998224725")).toBe(true);
  });

  it("recusa dígito verificador errado, tamanho errado e dígitos repetidos", () => {
    expect(isValidCpf("529.982.247-24")).toBe(false);
    expect(isValidCpf("529.982.247-15")).toBe(false);
    expect(isValidCpf("5299822472")).toBe(false);
    expect(isValidCpf("529982247250")).toBe(false);
    expect(isValidCpf("111.111.111-11")).toBe(false);
    expect(isValidCpf("")).toBe(false);
  });
});

describe("withCpfMask", () => {
  it("mascara o valor do campo antes de repassar o evento ao react-hook-form", async () => {
    const onChange = vi.fn(async () => {});
    const field: UseFormRegisterReturn<"cpf"> = { name: "cpf", onChange, onBlur: vi.fn(), ref: vi.fn() };
    const input = document.createElement("input");
    input.value = "52998224725";

    await withCpfMask(field).onChange({ target: input, type: "change" });

    expect(input.value).toBe("529.982.247-25");
    expect(onChange).toHaveBeenCalledOnce();
  });
});

describe("applyApiErrors", () => {
  it("leva cada campo do erro da API para o formulário, com o mapeamento de nomes", () => {
    const setError = vi.fn();
    const error = new ApiError(422, "validation_error", "Dados inválidos.", {
      cpf: "CPF já cadastrado.",
      birth_date: "Data inválida.",
    });

    expect(applyApiErrors(error, setError, { birth_date: "birthDate" })).toBe(true);
    expect(setError).toHaveBeenCalledTimes(2);
    expect(setError).toHaveBeenCalledWith(
      "cpf",
      { type: "server", message: "CPF já cadastrado." },
      { shouldFocus: true },
    );
    expect(setError).toHaveBeenCalledWith(
      "birthDate",
      { type: "server", message: "Data inválida." },
      { shouldFocus: true },
    );
  });

  it("devolve false quando não há o que aplicar", () => {
    const setError = vi.fn();
    expect(applyApiErrors(new ApiError(409, "conflict", "Conflito."), setError)).toBe(false);
    expect(applyApiErrors(new Error("falha"), setError)).toBe(false);
    expect(setError).not.toHaveBeenCalled();
  });
});
