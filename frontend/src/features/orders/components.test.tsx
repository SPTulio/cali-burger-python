import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ordersApi } from "@/api/endpoints";
import { OrderActions } from "@/features/orders/components";
import type { Order } from "@/types/api";

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

function order(overrides: Partial<Order> = {}): Order {
  return {
    id: 42,
    status: "awaiting_acceptance",
    customer_id: 1,
    customer_name: "João Silva",
    delivery_address: "Rua A, 1",
    total: "22.00",
    created_at: "2026-10-19T15:00:00Z",
    updated_at: "2026-10-19T15:00:00Z",
    items: [],
    payment: null,
    status_reason: null,
    events: null,
    available_actions: ["accept", "reject"],
    ...overrides,
  };
}

function renderActions(value: Order) {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <OrderActions order={value} />
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

describe("OrderActions", () => {
  beforeEach(() => {
    vi.spyOn(ordersApi, "act").mockResolvedValue({
      order: order({ status: "rejected", available_actions: [] }),
      message: "Pedido nº 42 recusado.",
    });
  });

  it("não recusa sem motivo e mostra o erro junto ao campo", async () => {
    const user = renderActions(order());
    await user.click(screen.getByRole("button", { name: "Recusar" }));
    const dialog = await screen.findByRole("alertdialog");
    await user.click(screen.getAllByRole("button", { name: "Recusar" }).at(-1)!);

    expect(await screen.findByText("Informe o motivo da recusa.")).toBeInTheDocument();
    expect(ordersApi.act).not.toHaveBeenCalled();
    expect(dialog).toBeInTheDocument();
  });

  it("envia o motivo escolhido ou digitado", async () => {
    const user = renderActions(order());
    await user.click(screen.getByRole("button", { name: "Recusar" }));
    await user.selectOptions(await screen.findByRole("combobox"), "Outro motivo");
    await user.type(screen.getByLabelText("Descreva o motivo"), "Sem gás para a chapa");
    await user.click(screen.getAllByRole("button", { name: "Recusar" }).at(-1)!);

    await waitFor(() =>
      expect(ordersApi.act).toHaveBeenCalledWith(42, "reject", "Sem gás para a chapa"),
    );
  });

  it("aceitar não pede motivo", async () => {
    const user = renderActions(order());
    await user.click(screen.getByRole("button", { name: "Aceitar" }));
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "Aceitar" }).at(-1)!);
    await waitFor(() => expect(ordersApi.act).toHaveBeenCalledWith(42, "accept", null));
  });
});
