# 06 · Migração dos dados do sistema PHP

O banco original (`db_caliburger`) **não é alterado**. O script [`backend/scripts/import_legacy.py`](../backend/scripts/import_legacy.py) lê os dados em uma transação somente leitura e grava no banco novo em **uma única transação** (se algo falhar, nada é importado).

## Como executar

```bash
cd backend
alembic upgrade head            # banco novo vazio e migrado
python -m scripts.import_legacy \
  --legacy-url "mysql+pymysql://usuario:senha@host:3306/db_caliburger" \
  --images-dir "../cali-burger/public/imagens/lanches" \
  --dry-run                     # simula; remova para gravar
```

O script se recusa a rodar se o banco de destino já tiver usuários, itens, ingredientes ou pedidos.

## Mapeamento

| Origem (PHP) | Destino | Observações |
| --- | --- | --- |
| `categoria` | `categories` | Associadas pelo nome às categorias criadas pela migração; nomes novos são criados. |
| `estoque` | `ingredients` | Ids preservados. |
| `cardapio` | `menu_items` | Ids preservados; imagens copiadas de `--images-dir` para `media/menu/`. |
| `cardapio_ingrediente` | `recipe_items` | — |
| `cliente` | `users` (`customer`) + `customer_addresses` | Ids novos; `login` → `username`. |
| `balconista_dono` | `users` (`manager`) | CPF repetido em balconista e cozinheiro: mantido como balconista, com aviso (D01). |
| `cozinheiro` | `users` (`cook`) | — |
| `senha` (todas as tabelas) | `password_hash` | Hashes bcrypt `$2y$` são mantidos (compatíveis); senhas legadas em texto puro são convertidas em hash. |
| `pedido` | `orders` | **Números dos pedidos preservados**; data convertida da hora local (`TIMEZONE`) para UTC; `delivery_address` fica vazio (não existia). |
| status `Aguardando aceitação` / `Em preparação` / `A caminho` / `Concluído` | `awaiting_acceptance` / `in_preparation` / `out_for_delivery` / `completed` | — |
| status `Cancelado/recusado` | `cancelled` | Não é possível saber se foi o cliente ou a loja (D02). |
| `itens_pedido` | `order_items` | `unit_price = valor / quantidade`. |
| `pedido_estoque` | `order_consumptions` | Pedidos pendentes importados podem ser recusados/cancelados e devolvem o estoque corretamente. |
| `pagamento` | `payments` | Um por pedido (o primeiro, se houver mais). |
| — | `order_status_events` | Um evento com o status atual e a data do pedido (o original não tinha histórico). |

## Verificação

`backend/tests/test_import_legacy.py` carrega os arquivos SQL originais do repositório PHP (`tests/fixtures/legacy/`) em um banco temporário, importa e confere: contagens, status, estoque, preservação dos números, conversão de fuso, senhas `$2y$` funcionando no login e devolução de estoque de um pedido importado.
