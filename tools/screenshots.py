"""Gera as capturas de tela do README (docs/img) com o Playwright.

Pré-requisitos: API e frontend rodando (http://127.0.0.1:5173) com o seed de demonstração,
`pip install playwright` e um Chrome/Chromium instalado.

    python tools/screenshots.py                  # usa o Google Chrome instalado
    python tools/screenshots.py --chromium       # usa o Chromium do Playwright

As contas usadas são as de demonstração (dados fictícios do seed).
"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright

BASE = "http://127.0.0.1:5173"
OUT = Path(__file__).resolve().parents[1] / "docs" / "img"
DEMO_PASSWORD = "cali1234"
ACCOUNTS = {"cliente": "joao", "balconista": "352.658.110-01", "cozinheiro": "211.996.250-27"}


def login(context: BrowserContext, who: str) -> None:
    context.clear_cookies()
    response = context.request.post(
        f"{BASE}/api/v1/auth/login",
        data={"identifier": ACCOUNTS[who], "password": DEMO_PASSWORD},
    )
    assert response.ok, response.text()


def shot(page: Page, path: str, name: str, *, wait_for: str | None = None, full: bool = False) -> None:
    page.goto(f"{BASE}{path}")
    page.wait_for_load_state("networkidle")
    if wait_for:
        page.wait_for_selector(wait_for)
    page.wait_for_timeout(400)  # imagens e animações curtas
    page.screenshot(path=OUT / f"{name}.png", full_page=full)
    print("ok", name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=None if args.chromium else "chrome")
        desktop = browser.new_context(
            viewport={"width": 1366, "height": 860}, color_scheme="light", locale="pt-BR"
        )
        desktop.add_init_script("localStorage.setItem('cb-theme', 'light')")
        page = desktop.new_page()

        # Cliente
        login(desktop, "cliente")
        shot(page, "/", "cardapio", wait_for="text=Cali Clássico")
        cart = {
            "state": {
                "lines": [
                    {"menuItemId": item["id"], "name": item["name"], "price": item["price"],
                     "imageUrl": item["image_url"], "quantity": qty, "notes": notes}
                    for item, qty, notes in zip(
                        desktop.request.get(f"{BASE}/api/v1/menu-items").json()[1:4],
                        (2, 1, 1),
                        ("Sem cebola", "", ""),
                        strict=True,
                    )
                ]
            },
            "version": 1,
        }
        page.evaluate("cart => localStorage.setItem('cb-cart', cart)", json.dumps(cart))
        shot(page, "/checkout", "checkout", wait_for="text=Confirmar pagamento")
        page.evaluate("localStorage.removeItem('cb-cart')")
        orders = desktop.request.get(f"{BASE}/api/v1/orders?page_size=5").json()["items"]
        shot(page, f"/pedidos/{orders[0]['id']}", "pedido", wait_for="text=Itens")

        # Balconista
        login(desktop, "balconista")
        shot(page, "/painel/pedidos", "painel-pedidos", wait_for="text=Aguardando aceitação")
        shot(page, "/painel/relatorios", "relatorio", wait_for="text=Faturamento por dia")
        shot(page, "/painel/estoque", "estoque", wait_for="text=Entrada de estoque")
        shot(page, "/painel/cardapio", "cardapio-gestao", wait_for="text=Cali Duplo")

        # Cozinha (tema escuro)
        dark = browser.new_context(
            viewport={"width": 1366, "height": 860}, color_scheme="dark", locale="pt-BR"
        )
        dark.add_init_script("localStorage.setItem('cb-theme', 'dark')")
        login(dark, "cozinheiro")
        shot(dark.new_page(), "/cozinha", "cozinha-escuro", wait_for="text=Fila da cozinha")

        # Celular
        mobile = browser.new_context(
            viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True,
            has_touch=True, color_scheme="light", locale="pt-BR",
        )
        mobile.add_init_script("localStorage.setItem('cb-theme', 'light')")
        login(mobile, "cliente")
        shot(mobile.new_page(), "/", "celular-cardapio", wait_for="text=Cali Clássico")

        browser.close()


if __name__ == "__main__":
    main()
