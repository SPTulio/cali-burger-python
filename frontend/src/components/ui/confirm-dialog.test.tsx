import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConfirmDialog } from "@/components/ui/confirm-dialog";

/** Promessa controlada pelo teste, para segurar o onConfirm "em andamento". */
function deferred() {
  let resolve!: () => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function setup(onConfirm: () => unknown) {
  const onOpenChange = vi.fn();
  render(
    <ConfirmDialog
      open
      onOpenChange={onOpenChange}
      title="Cancelar pedido?"
      description="O pedido não poderá ser retomado."
      confirmLabel="Cancelar pedido"
      destructive
      onConfirm={onConfirm}
    />,
  );
  return {
    user: userEvent.setup(),
    onOpenChange,
    confirm: screen.getByRole("button", { name: "Cancelar pedido" }),
    back: screen.getByRole("button", { name: "Voltar" }),
  };
}

describe("ConfirmDialog", () => {
  it("não envia duas vezes enquanto onConfirm está pendente", async () => {
    const pending = deferred();
    const onConfirm = vi.fn(() => pending.promise);
    const { user, onOpenChange, confirm, back } = setup(onConfirm);

    await user.click(confirm);
    expect(confirm).toBeDisabled();
    expect(confirm).toHaveAttribute("aria-busy", "true");
    expect(back).toBeDisabled();

    await user.click(confirm);
    await user.dblClick(confirm);
    // Esc também não fecha no meio do envio.
    await user.keyboard("{Escape}");
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onOpenChange).not.toHaveBeenCalled();

    pending.resolve();
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
    expect(onOpenChange).toHaveBeenCalledTimes(1);
    expect(confirm).toBeEnabled();
  });

  it("mantém o diálogo aberto e libera o botão se onConfirm falhar", async () => {
    const pending = deferred();
    const onConfirm = vi.fn(() => pending.promise);
    const { user, onOpenChange, confirm } = setup(onConfirm);

    await user.click(confirm);
    pending.reject(new Error("falhou"));

    await waitFor(() => expect(confirm).toBeEnabled());
    expect(onOpenChange).not.toHaveBeenCalled();

    await user.click(confirm);
    expect(onConfirm).toHaveBeenCalledTimes(2);
  });

  it("fecha pelo botão Voltar quando não há envio em andamento", async () => {
    const onConfirm = vi.fn();
    const { user, onOpenChange, back } = setup(onConfirm);

    await user.click(back);
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onConfirm).not.toHaveBeenCalled();
  });
});
