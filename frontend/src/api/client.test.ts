import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, errorMessage, http } from "@/api/client";

const fetchMock = vi.fn<typeof fetch>();

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Cabeçalhos enviados na última chamada a fetch. */
function sentHeaders(): Record<string, string> {
  const init = fetchMock.mock.lastCall?.[1];
  return (init?.headers ?? {}) as Record<string, string>;
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
  fetchMock.mockImplementation(async () => jsonResponse(200, { ok: true }));
  // Valor do cookie vem codificado, como o servidor envia.
  document.cookie = "cb_csrf=abc%2B123";
});

afterEach(() => {
  document.cookie = "cb_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

describe("token CSRF", () => {
  it("não vai em GET", async () => {
    await http.get("/menu");
    expect(sentHeaders()).not.toHaveProperty("X-CSRF-Token");
  });

  it.each([
    ["POST", http.post],
    ["PUT", http.put],
    ["DELETE", http.delete],
  ] as const)("vai em %s, decodificado do cookie", async (method, call) => {
    await call("/orders", { json: { items: [] } });
    expect(fetchMock.mock.lastCall?.[1]?.method).toBe(method);
    expect(sentHeaders()["X-CSRF-Token"]).toBe("abc+123");
  });

  it("é omitido quando o cookie não existe", async () => {
    document.cookie = "cb_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    await http.post("/auth/login", { json: {} });
    expect(sentHeaders()).not.toHaveProperty("X-CSRF-Token");
  });
});

describe("requisição", () => {
  it("monta a URL com os parâmetros e serializa o JSON", async () => {
    await http.post("/orders", {
      json: { a: 1 },
      params: { status: ["new", "ready"], page: 2, q: "", empty: null },
    });
    const [url, init] = fetchMock.mock.lastCall!;
    expect(url).toBe("/api/v1/orders?status=new&status=ready&page=2");
    expect(init?.body).toBe('{"a":1}');
    expect(init?.credentials).toBe("same-origin");
    expect(sentHeaders()["Content-Type"]).toBe("application/json");
  });

  it("devolve undefined em 204", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await expect(http.delete("/cart")).resolves.toBeUndefined();
  });
});

describe("erros", () => {
  it("converte o corpo de erro da API em ApiError", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(422, {
        error: { code: "validation_error", message: "Dados inválidos.", fields: { cpf: "CPF inválido." } },
      }),
    );
    const error = await http.post("/auth/register", { json: {} }).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 422,
      code: "validation_error",
      message: "Dados inválidos.",
      fields: { cpf: "CPF inválido." },
    });
    expect(errorMessage(error)).toBe("Dados inválidos.");
  });

  it("usa mensagem genérica quando o corpo não é JSON", async () => {
    fetchMock.mockResolvedValueOnce(new Response("<html>Bad Gateway</html>", { status: 502 }));
    await expect(http.get("/menu")).rejects.toMatchObject({
      status: 502,
      code: "unknown_error",
      message: "Ocorreu um erro inesperado. Tente novamente.",
      fields: {},
    });
  });

  it("transforma falha de rede em ApiError com status 0", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(http.get("/menu")).rejects.toMatchObject({ status: 0, code: "network_error" });
  });

  it("repassa o cancelamento sem convertê-lo", async () => {
    fetchMock.mockRejectedValueOnce(new DOMException("aborted", "AbortError"));
    await expect(http.get("/menu")).rejects.toMatchObject({ name: "AbortError" });
  });
});
