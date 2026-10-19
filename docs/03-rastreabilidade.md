# 03 · Matriz de rastreabilidade

Relaciona cada funcionalidade (F) e regra (R) do sistema PHP ([01-auditoria.md](01-auditoria.md)) à implementação no novo sistema. Coluna **Testes** aponta os arquivos em `backend/tests/` que cobrem o item. Todas as telas também foram percorridas manualmente no navegador (desktop e 375 px).

| ID | Funcionalidade original | Endpoint(s) | Tela (frontend) | Testes | Status |
| --- | --- | --- | --- | --- | --- |
| F01 | Cadastro de cliente | `POST /auth/register` | `/cadastro` | `test_auth.py` | ✅ |
| F02 | Login de cliente (usuário) | `POST /auth/login` | `/entrar` | `test_auth.py` | ✅ unificado |
| F03 | Login de funcionário (CPF) | `POST /auth/login` | `/entrar` | `test_auth.py` | ✅ unificado |
| F04 | Bloqueio por tentativas | `POST /auth/login` (429) | mensagem no formulário | `test_auth.py` | ✅ melhorado (IP + identificador, no banco) |
| F05 | Senhas legadas | `scripts/import_legacy.py` | — | `test_import_legacy.py` | ✅ movido para a importação |
| F06 | Logout | `POST /auth/logout` | menu do usuário | `test_auth.py` | ✅ |
| F07 | Cardápio com categorias e disponibilidade | `GET /categories`, `GET /menu-items` | `/` (cardápio) | `test_catalog.py`, `test_unit_rules.py` | ✅ |
| F08 | Carrinho (soma, limite 20, observação, remover) | validação em `POST /orders` | gaveta do carrinho + `/carrinho` | `test_unit_rules.py`, `test_orders.py` | ✅ carrinho no navegador |
| F09 | Revisão: endereço + resumo + PIX ilustrativo | `GET /me/profile`, `PUT /me/address` | `/checkout` | `test_accounts.py` | ✅ |
| F10 | Criação transacional com baixa de estoque | `POST /orders` | `/checkout` | `test_orders.py`, `test_concurrency.py` | ✅ + idempotência |
| F11 | Confirmação do pedido | `GET /orders/{id}` | `/pedidos/{id}?novo=1` | `test_orders.py` | ✅ |
| F12 | Meus pedidos, filtros, cancelar, recebi | `GET /orders`, `POST /orders/{id}/actions/{cancel,complete}` | `/pedidos` | `test_orders.py` | ✅ + paginação e linha do tempo |
| F13 | Perfil do cliente, senha, endereço, excluir conta | `/me/*` | `/perfil` | `test_accounts.py` | ✅ |
| F14 | Pedidos do balconista (aguardando / todos + filtros) | `GET /orders` | `/painel/pedidos` | `test_orders.py` | ✅ + busca, intervalo de datas, paginação |
| F15 | Aceitar / recusar / enviar | `POST /orders/{id}/actions/{accept,reject,dispatch}` | `/painel/pedidos` | `test_orders.py` | ✅ |
| F16 | Contador de aguardando | `GET /orders/summary` | badge na navegação | `test_orders.py` | ✅ atualização automática |
| F17 | CRUD do cardápio com receita | `/menu-items` | `/painel/cardapio` | `test_catalog.py` | ✅ |
| F18 | Upload seguro de imagem | `PUT /menu-items/{id}/image` | formulário do item | `test_catalog.py` | ✅ + remove arquivo antigo |
| F19 | Estoque (listar, somar, editar, excluir) | `/ingredients` | `/painel/estoque` | `test_inventory.py` | ✅ |
| F20 | Relatório de vendas | `GET /reports/sales` | `/painel/relatorios` | `test_reports.py` | ✅ + gráfico de faturamento diário |
| F21 | Equipe (listar, cadastrar, excluir; último balconista) | `/staff` | `/painel/equipe` | `test_staff.py` | ✅ |
| F22 | Perfil do funcionário + senha | `/me/profile`, `/me/password` | `/painel/perfil`, `/cozinha/perfil` | `test_accounts.py` | ✅ |
| F23 | Balconista exclui a própria conta | `DELETE /me` | `/painel/perfil` | `test_accounts.py` | ✅ |
| F24 | Fila da cozinha (auto-atualização) | `GET /orders?sort=oldest` (para o cozinheiro, o servidor restringe à fila de preparo), `POST …/ready` | `/cozinha` | `test_orders.py` | ✅ atualização a cada 15 s sem recarregar; ⚠️ a cozinha marca “Pronto” e o balcão despacha (ver abaixo) |
| F25 | Cardápio somente leitura (cozinha) | `GET /menu-items` | `/cozinha/cardapio` | `test_catalog.py` | ✅ |
| F26 | Confirmação de ações destrutivas | — | `ConfirmDialog` | — (verificação manual) | ✅ |
| F27 | Mensagens de sucesso/erro | formato de erro único | toasts + erros por campo | — | ✅ |

| Regra | Onde está implementada |
| --- | --- |
| R01 transições condicionais | `orders/state_machine.py` (tabela de ações) + `orders/service.py::apply_action` (linha travada com `FOR UPDATE`) |
| R02–R03 criação transacional, centavos | `orders/service.py::create_order` (ingredientes travados em ordem de id; `Decimal`) |
| R04–R05 carrinho | `orders/schemas.py` (limites) + `create_order` (itens inexistentes) + `features/cart` |
| R06 pagamento PIX | `payments` gravado em `create_order` |
| R07 exclusão de conta mantém pedidos | FK `SET NULL` + `customer_name` congelado |
| R08 disponibilidade | `catalog/service.py::list_menu_items` (uma consulta agregada) + `catalog/rules.py` |
| R09–R11 itens do cardápio | `catalog/schemas.py`, `catalog/service.py` |
| R12–R14 estoque | `inventory/service.py`, `CHECK` no banco |
| R15–R18 relatório | `reports/service.py` |
| R19–R23 validações de pessoas | `core/validators.py`, schemas de `auth`, `accounts`, `staff` |
| R24 último balconista | `staff/service.py::ensure_not_last_manager` (usado por `DELETE /staff/{id}` e `DELETE /me`) |
| R25–R26 isolamento | dependências de perfil + consultas filtradas pelo usuário da sessão |
| R27 mensagem genérica de login | `auth/service.py::authenticate` |

## Fase 1 do roteiro de evolução

Funcionalidades novas, sem equivalente no sistema PHP, vindas do roteiro de [07-analise-de-mercado.md](07-analise-de-mercado.md#5-roteiro-sugerido). O número entre parênteses é o da sugestão naquele documento.

| ID | Funcionalidade | Endpoint(s) | Tela (frontend) | Testes |
| --- | --- | --- | --- | --- |
| N01 | Horário de funcionamento (26) | `GET /store`, `PUT /store/hours` | `/painel/loja`, aviso no topo do cardápio, bloqueio no checkout | `test_store.py`, `test_unit_rules.py` |
| N02 | Pausar a loja e itens (27) | `PUT /store/pause`, `PUT /menu-items/{id}/pause` | `/painel/loja`, `/painel/cardapio` | `test_store.py`, `test_catalog.py` |
| N03 | Motivo de recusa e de cancelamento (28) | `POST /orders/{id}/actions/{reject,cancel}` com `{reason}` | diálogos de recusa/cancelamento; motivo no detalhe e nas listas | `test_orders.py`, `components.test.tsx` |
| N04 | “Peça de novo” (18) | — (usa `GET /orders` e `GET /menu-items`) | faixa “Peça de novo” no cardápio, botão em “Meus pedidos” e no detalhe | `reorder.test.ts` |
| N05 | Retirada no balcão (10) | `POST /orders` com `fulfillment=pickup`, `…/pick_up` | escolha no checkout; selo “Retirada” no balcão e na cozinha | `test_orders.py`, `test_unit_rules.py` |
| N06 | Status “Pronto” e cronômetro da cozinha (32, 33) | `…/ready`; `status_since` no pedido | `/cozinha` (cores por tempo de preparo), aba “Prontos” no balcão | `test_orders.py`, `timer.test.ts` |
| N07 | Taxa por bairro, frete grátis e previsão (8, 9) | `GET /store/quote`, `GET/PUT /store/zones`, `PUT /store/settings` | checkout, cardápio, detalhe do pedido, `/painel/loja` | `test_delivery.py` |
| N08 | Política de Privacidade e aceite (51) | `POST /auth/register` com `accept_privacy` | `/privacidade`, caixa no cadastro, data do aceite no perfil | `test_auth.py` |

**Mudança de regra:** no sistema PHP o cozinheiro enviava o pedido para entrega (`Em preparação → A caminho`). Agora o cozinheiro marca **Pronto** e o **balconista** despacha (entrega) ou entrega no balcão (retirada). O motivo: quem sai com o pedido é o balcão, e só ele sabe quando o entregador chegou ou o cliente veio buscar. O cozinheiro deixa de ver o pedido na fila assim que ele fica pronto.

## Melhorias sem alteração de regra de negócio

| Melhoria | Motivo |
| --- | --- |
| Status `rejected` separado de `cancelled` | o cliente entende se foi ele ou a loja; ambos continuam fora do relatório e devolvem estoque |
| Linha do tempo do pedido | rastreabilidade (quem aceitou, quando saiu) |
| Idempotência na criação | evita pedido duplicado por duplo clique ou reenvio |
| Paginação/filtros no servidor | listas crescem com o tempo |
| Endereço congelado no pedido | o pedido mostra para onde foi entregue mesmo se o cliente mudar o endereço depois |
