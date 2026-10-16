# 03 · Matriz de rastreabilidade

Relaciona cada funcionalidade (F) e regra (R) do sistema PHP ([01-auditoria.md](01-auditoria.md)) à implementação no novo sistema. Coluna **Testes** aponta os arquivos em `backend/tests/` que cobrem o item.

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
| F24 | Fila da cozinha (auto-atualização) | `GET /orders?scope=kitchen`, `POST …/dispatch` | `/cozinha` | `test_orders.py` | ✅ atualização a cada 15 s sem recarregar |
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

## Melhorias sem alteração de regra de negócio

| Melhoria | Motivo |
| --- | --- |
| Status `rejected` separado de `cancelled` | o cliente entende se foi ele ou a loja; ambos continuam fora do relatório e devolvem estoque |
| Linha do tempo do pedido | rastreabilidade (quem aceitou, quando saiu) |
| Idempotência na criação | evita pedido duplicado por duplo clique ou reenvio |
| Paginação/filtros no servidor | listas crescem com o tempo |
| Endereço congelado no pedido | o pedido mostra para onde foi entregue mesmo se o cliente mudar o endereço depois |
