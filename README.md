# Cali Burger

[![CI](https://github.com/SPTulio/cali-burger-python/actions/workflows/ci.yml/badge.svg)](https://github.com/SPTulio/cali-burger-python/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776ab)
![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688)
![React 19](https://img.shields.io/badge/React-19-149eca)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178c6)
![MySQL 8](https://img.shields.io/badge/MySQL-8.4-4479a1)

Sistema de pedidos para uma hamburgueria: o cliente monta o pedido pelo cardápio e paga via PIX (simulado), o balcão aceita, a cozinha prepara e o **estoque de ingredientes é baixado automaticamente pela receita de cada item** — com devolução exata quando o pedido é cancelado ou recusado.

É a reconstrução completa, em **Python + React + MySQL**, de um sistema acadêmico feito originalmente em PHP ([SPTulio/cali-burger](https://github.com/SPTulio/cali-burger)). As regras de negócio foram preservadas; arquitetura, interface, segurança e testes foram refeitos do zero. A análise do sistema antigo e as decisões da nova versão estão documentadas em [`docs/`](docs).

![Painel de pedidos do balconista](docs/img/painel-pedidos.png)

## Funcionalidades

| Perfil | O que faz |
| --- | --- |
| **Cliente** | Navega pelo cardápio (público) com disponibilidade em tempo real (“Esgotado”, “Últimas N”), monta o carrinho com observações por item, revisa endereço e paga via PIX simulado; acompanha o pedido em uma linha do tempo, cancela enquanto aguarda e confirma o recebimento. Edita dados, endereço e senha; pode excluir a conta. |
| **Balconista / dono** | Aceita ou recusa pedidos (fila com contador atualizado sozinho), consulta todos os pedidos com busca, filtros e paginação; gerencia o cardápio (receitas e fotos), o estoque e a equipe; vê o relatório de vendas por período. |
| **Cozinheiro** | Vê a fila de preparo (do mais antigo para o mais novo, com tempo de espera) e envia os pedidos para entrega; consulta receitas e disponibilidade. |

**Fluxo do pedido:** `Aguardando aceitação → Em preparação → A caminho → Concluído`, além de `Cancelado` (pelo cliente) e `Recusado` (pela loja). Quem pode executar cada ação é definido em uma máquina de estados no servidor ([`state_machine.py`](backend/app/modules/orders/state_machine.py)).

**Estoque integrado:** cada item tem uma receita. Ao finalizar o pedido, as linhas de estoque são travadas (`SELECT … FOR UPDATE`) e o consumo do pedido inteiro é conferido e baixado em uma única transação; dois pedidos simultâneos não conseguem usar o mesmo ingrediente (há teste de concorrência para isso).

<table>
  <tr>
    <td><img src="docs/img/cardapio.png" alt="Cardápio do cliente"></td>
    <td><img src="docs/img/checkout.png" alt="Revisão do pedido e pagamento"></td>
  </tr>
  <tr>
    <td><img src="docs/img/pedido.png" alt="Acompanhamento do pedido"></td>
    <td><img src="docs/img/cozinha-escuro.png" alt="Fila da cozinha (tema escuro)"></td>
  </tr>
  <tr>
    <td><img src="docs/img/relatorio.png" alt="Relatório de vendas"></td>
    <td><img src="docs/img/estoque.png" alt="Estoque"></td>
  </tr>
</table>

<p align="center"><img src="docs/img/celular-cardapio.png" alt="Cardápio no celular" width="280"></p>

## Tecnologias

| Camada | Escolhas | Por quê |
| --- | --- | --- |
| API | **FastAPI**, Pydantic v2, SQLAlchemy 2 (ORM tipado), Alembic, PyMySQL, bcrypt, Pillow | Contratos validados e documentados automaticamente (OpenAPI), consultas parametrizadas, migrações versionadas, senhas compatíveis com os hashes do PHP. |
| Banco | **MySQL 8** (InnoDB, utf8mb4) | Mantido do sistema original; `CHECK`, chaves estrangeiras e índices protegem a consistência. |
| Web | **React 19 + TypeScript** (strict), Vite, Tailwind CSS v4, Radix UI, TanStack Query, React Hook Form + Zod, Zustand, Lucide | Componentes acessíveis, cache e sincronização com a API, validação imediata nos formulários. |
| Qualidade | pytest (121 testes em MySQL real), Vitest + Testing Library, ruff, mypy strict, ESLint, GitHub Actions | Regras de negócio, permissões, concorrência, migrações e importação testadas; carrinho, validações, cliente HTTP e componentes críticos do frontend também. |
| Execução | Docker Compose (MySQL + API + Nginx) | Ambiente reproduzível com um comando. |

Justificativas detalhadas em [`docs/05-decisoes.md`](docs/05-decisoes.md).

## Arquitetura

```mermaid
flowchart LR
    B[Navegador<br/>React + TypeScript] -- "/api/v1 (JSON)<br/>cookie HttpOnly + CSRF" --> N[Nginx]
    N --> A[FastAPI]
    A -- SQLAlchemy 2 --> M[(MySQL 8)]
    A --> F[(media/<br/>imagens do cardápio)]
```

- **Backend em módulos de domínio** (`auth`, `accounts`, `staff`, `catalog`, `inventory`, `orders`, `reports`), cada um com `router` (HTTP) → `service` (regras e transações) → `models`. Rotas não contêm SQL nem regra de negócio.
- **Erros padronizados** `{"error": {"code", "message", "fields"}}`; erros de campo aparecem junto ao input no frontend.
- **Frontend por funcionalidade** (`features/*`), cliente HTTP central (`src/api`), design system em `components/ui`, rotas protegidas por perfil e telas da equipe carregadas sob demanda.

Detalhes: [`docs/02-arquitetura.md`](docs/02-arquitetura.md) · Design system: [`docs/04-design-system.md`](docs/04-design-system.md)

### Banco de dados

```mermaid
erDiagram
    users ||--o| customer_addresses : endereço
    users ||--o{ sessions : sessões
    users |o--o{ orders : "faz (SET NULL)"
    categories ||--o{ menu_items : agrupa
    menu_items ||--o{ recipe_items : receita
    ingredients ||--o{ recipe_items : "usado em"
    orders ||--|{ order_items : contém
    orders ||--o{ order_consumptions : consumiu
    ingredients ||--o{ order_consumptions : baixa
    orders ||--|| payments : pagamento
    orders ||--o{ order_status_events : "linha do tempo"
```

Nome, preço e subtotal de cada item ficam gravados no pedido: mudar ou excluir um item do cardápio não altera o histórico.

## Como executar

### Com Docker (recomendado)

Pré-requisito: Docker com Docker Compose.

```bash
git clone https://github.com/SPTulio/cali-burger-python.git
cd cali-burger-python
cp .env.example .env          # troque as senhas
docker compose up -d --build
docker compose exec api python -m scripts.seed_demo   # opcional: dados de demonstração
```

Acesse **http://localhost:8080** · API: http://localhost:8080/api/docs

### Sem Docker

Pré-requisitos: Python 3.12+, Node.js 22+ e MySQL 8.

**1. Banco de dados** — crie o banco da aplicação e um banco **separado** para os testes:

```sql
CREATE DATABASE caliburger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE caliburger_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'caliburger'@'%' IDENTIFIED BY 'troque-esta-senha';
GRANT ALL PRIVILEGES ON caliburger.* TO 'caliburger'@'%';
GRANT ALL PRIVILEGES ON caliburger_test.* TO 'caliburger'@'%';
-- só para o teste de importação do banco PHP:
GRANT ALL PRIVILEGES ON caliburger_legacy_test.* TO 'caliburger'@'%';
```

**2. API**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                 # ajuste DATABASE_URL e TEST_DATABASE_URL
alembic upgrade head
python -m scripts.seed_demo          # opcional: dados de demonstração
uvicorn app.main:app --reload --port 8000
```

**3. Frontend** (em outro terminal)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Acesse **http://127.0.0.1:5173**. O Vite repassa `/api` e `/media` para a API, então tudo funciona no mesmo endereço (sem CORS).

### Contas de demonstração

Criadas por `scripts/seed_demo.py` (dados **fictícios**; senha de todas: `cali1234`). A tela de login tem botões que preenchem cada conta.

| Perfil | Entrar com |
| --- | --- |
| Cliente | usuário `joao` (ou `maria`, `pedro`) |
| Balconista / dono | CPF `352.658.110-01` |
| Cozinheiro | CPF `211.996.250-27` |

## Variáveis de ambiente

API (`backend/.env`, modelo em [`backend/.env.example`](backend/.env.example)):

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `DATABASE_URL` | — | URL do MySQL (`mysql+pymysql://usuario:senha@host:3306/caliburger?charset=utf8mb4`) |
| `TEST_DATABASE_URL` | — | Banco dos testes; o nome **precisa** terminar em `_test` (os testes apagam os dados dele) |
| `ENVIRONMENT` | `development` | `production` bloqueia o seed de demonstração |
| `CORS_ORIGINS` | vazio | Origens permitidas, separadas por vírgula (desnecessário com proxy) |
| `COOKIE_SECURE` | `false` | `true` em produção com HTTPS |
| `SESSION_IDLE_HOURS` / `SESSION_MAX_DAYS` | `12` / `7` | Expiração por inatividade / máxima da sessão |
| `LOW_STOCK_THRESHOLD` | `10` | Quantidade a partir da qual o ingrediente é “estoque baixo” |
| `TIMEZONE` | `America/Sao_Paulo` | Fuso usado nos filtros por data e no relatório |
| `MEDIA_DIR` | `backend/media` | Pasta das imagens enviadas |

Frontend (`frontend/.env`): `VITE_SHOW_DEMO_ACCOUNTS=true` mostra as contas de demonstração no login. Docker Compose (`.env` na raiz): senhas do MySQL e portas — veja [`.env.example`](.env.example).

## Testes e qualidade

```bash
cd backend
pytest                    # 121 testes contra o MySQL de teste
ruff check . && ruff format --check .
mypy app scripts          # modo strict

cd ../frontend
npm test                  # Vitest + Testing Library (jsdom)
npm run lint              # ESLint
npm run build             # TypeScript strict + build de produção
```

Os testes do backend cobrem: regras puras (CPF, disponibilidade, máquina de estados, dinheiro); endpoints e permissões de cada perfil; o fluxo completo do pedido com baixa exata de estoque; estoque insuficiente; idempotência; devolução de estoque ao cancelar/recusar; **dois pedidos simultâneos pelo último ingrediente**; relatório (cancelados fora, fuso e limites de data); sessões, CSRF, limite de tentativas e senhas legadas; upload de imagens maliciosas; migrações (`upgrade`/`downgrade` e sincronia com os modelos); e a importação dos dados do sistema PHP.

Os testes do frontend cobrem: o carrinho (soma ao adicionar, limite de 20 por item, sincronização com o cardápio, total em centavos); validação e máscara de CPF e o envio dos erros de campo da API para o formulário; formatação de moeda e de datas sem deslocamento de fuso (rodam em `America/Sao_Paulo`); o destino após o login, que recusa endereços externos como `//site`; o cliente HTTP (token CSRF só em métodos que alteram dados, conversão do corpo de erro em `ApiError`, falha de rede); e o diálogo de confirmação, que não envia duas vezes enquanto a ação está pendente.

## Exemplos de uso da API

Documentação interativa em `/api/docs` (Swagger) e `/api/redoc`.

```bash
API=http://127.0.0.1:8000/api/v1

# Cardápio público com disponibilidade
curl -s $API/menu-items | jq '.[] | {name, price, availability, portions}'

# Login (guarda os cookies de sessão e CSRF)
curl -s -c cookies.txt -H "Content-Type: application/json" \
  -d '{"identifier": "joao", "password": "cali1234"}' $API/auth/login
CSRF=$(awk '$6 == "cb_csrf" {print $7}' cookies.txt)

# Finalizar um pedido (a mesma Idempotency-Key devolve o mesmo pedido)
curl -s -b cookies.txt -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
  -H "Idempotency-Key: compra-0001-teste" \
  -d '{"items": [{"menu_item_id": 1, "quantity": 2, "notes": "sem cebola"}]}' \
  $API/orders
```

Exemplo de erro de regra de negócio:

```json
{
  "error": {
    "code": "insufficient_stock",
    "message": "Não há estoque suficiente para: Cali Duplo. Diminua a quantidade ou escolha outro item.",
    "fields": {}
  }
}
```

## Migração dos dados do sistema PHP

[`backend/scripts/import_legacy.py`](backend/scripts/import_legacy.py) importa o banco original sem alterá-lo, preservando números de pedidos e senhas (`$2y$` do PHP). Mapeamento e decisões em [`docs/06-migracao-dados.md`](docs/06-migracao-dados.md).

## Estrutura do repositório

```text
backend/
  app/            # FastAPI: core (config, erros, segurança), db, modules/<domínio>
  alembic/        # migrações
  scripts/        # seed de demonstração e importação do banco PHP
  tests/          # pytest (MySQL de teste)
frontend/
  src/            # api, app (rotas, layouts, guards), components/ui, features/<domínio>, lib
                  # testes Vitest ao lado do código (*.test.ts[x]); utilitários em src/test
docs/             # auditoria, arquitetura, rastreabilidade, design system, decisões, migração
tools/            # geração das capturas de tela (Playwright)
docker-compose.yml
```

## Documentação

1. [Auditoria do sistema PHP](docs/01-auditoria.md) — funcionalidades, regras, modelo de dados, problemas e dúvidas
2. [Arquitetura](docs/02-arquitetura.md) — módulos, contratos da API, autenticação, testes
3. [Matriz de rastreabilidade](docs/03-rastreabilidade.md) — cada funcionalidade original → endpoint, tela e teste
4. [Design system](docs/04-design-system.md) — tokens, componentes, responsividade e acessibilidade
5. [Decisões e limitações](docs/05-decisoes.md)
6. [Migração de dados](docs/06-migracao-dados.md)

## Limitações conhecidas

- O pagamento PIX é **simulado** e identificado assim na interface.
- Atualizações em tempo real por polling (sem WebSocket).
- Os testes automatizados do frontend são unitários e de componente; não há testes ponta a ponta no navegador. Os fluxos completos das telas foram verificados manualmente.

## Créditos

Sistema original (PHP) desenvolvido em equipe por Adnan Charif, Henrique Szlachta, Lucas Kumagae e Sérgio Pizzatto Tulio. Esta versão em Python/React foi reconstruída por **Sérgio Pizzatto Tulio** ([@SPTulio](https://github.com/SPTulio)) a partir do sistema original. As fotos dos produtos vêm do projeto original.
