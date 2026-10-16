# 04 · Design system

Identidade nova, sem reaproveitar o visual do sistema PHP. Princípios:

1. **Produtividade primeiro** — telas de operação (pedidos, estoque, cozinha) priorizam densidade, alinhamento e leitura rápida; a vitrine do cliente usa fotos e mais respiro.
2. **Cor com significado** — a cor da marca aparece em ações principais e na identidade; cores de status são reservadas ao estado do pedido/estoque.
3. **Um padrão por problema** — tabelas para listas operacionais, cartões só onde a unidade é visual (produto, ticket da cozinha), formulários em seções.

Os tokens vivem em [`frontend/src/styles/globals.css`](../frontend/src/styles/globals.css) (CSS custom properties expostas ao Tailwind v4 via `@theme`). Componentes em [`frontend/src/components/ui`](../frontend/src/components/ui).

## Cores (tokens semânticos)

| Token | Claro | Escuro | Uso |
| --- | --- | --- | --- |
| `--background` | `#FAFAF9` | `#0C0A09` | fundo da aplicação |
| `--surface` | `#FFFFFF` | `#1C1917` | cartões, tabelas, painéis |
| `--muted` | `#F5F5F4` | `#292524` | fundos secundários, hover de linha |
| `--border` | `#E7E5E4` | `#36312E` | divisórias e contornos |
| `--foreground` | `#1C1917` | `#FAFAF9` | texto principal (contraste 17:1) |
| `--muted-foreground` | `#57534E` | `#A8A29E` | texto secundário (≥ 7:1 no claro, ≥ 7:1 no escuro) |
| `--primary` | `#C2410C` | `#F97316` | marca “brasa”: CTA, links, foco |
| `--primary-foreground` | `#FFFFFF` | `#1C0A02` | texto sobre primária (5,2:1 / 7,9:1) |
| `--destructive` | `#DC2626` | `#F87171` | excluir, recusar |
| `--success` | `#047857` | `#34D399` | concluído, estoque OK |
| `--warning` | `#B45309` | `#FBBF24` | aguardando, estoque baixo |
| `--info` | `#1D4ED8` | `#60A5FA` | em preparação |
| `--ring` | primária | primária | anel de foco (2 px + offset) |

Status do pedido (badge = fundo suave + texto escuro do mesmo matiz + ponto):

| Status | Rótulo | Matiz |
| --- | --- | --- |
| `awaiting_acceptance` | Aguardando aceitação | âmbar |
| `in_preparation` | Em preparação | azul |
| `out_for_delivery` | A caminho | violeta |
| `completed` | Concluído | verde |
| `cancelled` | Cancelado | neutro |
| `rejected` | Recusado | vermelho |

Estoque: **OK** (verde) · **Baixo** (âmbar, ≤ limite) · **Em falta** (vermelho, 0). Disponibilidade no cardápio: **Esgotado** · **Últimas N** (≤ 5).

## Tipografia

Fonte **Inter Variable** (auto-hospedada via `@fontsource-variable/inter`, sem chamadas a serviços externos). Números monetários, quantidades e nº de pedido usam `tabular-nums`.

| Estilo | Tamanho / altura | Peso | Uso |
| --- | --- | --- | --- |
| Display | 30/36 | 700 | título da vitrine, KPIs |
| H1 (página) | 24/32 | 650 | título de página |
| H2 (seção) | 18/28 | 600 | seções, cabeçalho de cartão |
| Corpo | 14/20 | 400 | padrão da interface (tabelas, formulários) |
| Corpo grande | 16/24 | 400 | vitrine, textos de apoio |
| Legenda | 12/16 | 500 | rótulos auxiliares, cabeçalho de tabela (caixa alta, `tracking-wide`) |

## Espaçamento, raios e elevação

- Escala de 4 px (Tailwind): 1 = 4 px, 2 = 8, 3 = 12, 4 = 16, 6 = 24, 8 = 32, 12 = 48.
- Padding de página: 16 px (celular), 24 px (tablet), 32 px (desktop). Largura máxima de conteúdo: 1280 px (operação), 1120 px (vitrine), 720 px (formulários).
- Raios: `--radius-sm` 6 px (badges, inputs pequenos), `--radius-md` 8 px (botões, inputs), `--radius-lg` 12 px (cartões, diálogos).
- Elevação: `shadow-xs` (cartões, bordas sutis), `shadow-lg` (menus, popovers, diálogos). Sem sombras empilhadas nem gradientes decorativos.

## Componentes

| Componente | Variantes / estados |
| --- | --- |
| `Button` | `primary`, `secondary`, `outline`, `ghost`, `destructive`, `link`; tamanhos `sm` (32 px), `md` (36 px), `lg` (44 px, vitrine/mobile), `icon`; estado `loading` (spinner + `aria-busy`, desabilita), `disabled` (50% opacidade, sem ponteiro) |
| `Input`, `Textarea`, `Select` (Radix) | altura 36 px; borda `--border`; foco com anel primário; inválido com borda e texto `--destructive` + `aria-invalid` |
| `FormField` | rótulo, descrição opcional, mensagem de erro ligada por `aria-describedby` |
| `Table` | cabeçalho em legenda caixa alta; números alinhados à direita; linhas com hover; ações contextuais na última coluna (menu “…” ou botões compactos); rolagem horizontal em telas estreitas |
| `Pagination` | “Mostrando 1–20 de 134”, anterior/próxima, tamanho de página |
| `Badge` / `StatusBadge` | neutro, sucesso, aviso, perigo, info, violeta |
| `Dialog`, `ConfirmDialog` | foco preso, `Esc` fecha, botão destrutivo à direita, ação em andamento bloqueia duplo envio |
| `Sheet` | gaveta lateral (carrinho, navegação mobile) |
| `DropdownMenu` | menu do usuário, ações de linha |
| `Tabs` | visões (Aguardando / Todos) |
| `EmptyState` | ícone, título, texto orientando a próxima ação, CTA opcional |
| `Skeleton` | carregamento de listas e cartões |
| `Toast` (Sonner) | sucesso/erro após ações; erros de campo ficam no formulário |
| `PageHeader` | título, descrição, ações primárias à direita |
| `QuantityStepper` | −/+ com limites, rótulo acessível |

## Navegação

- **Cliente**: cabeçalho fixo (logo, Cardápio, Meus pedidos, botão do carrinho com contador, menu do usuário); categorias em “chips” fixos abaixo do cabeçalho; carrinho em gaveta lateral.
- **Balconista e cozinha**: barra lateral (240 px) com seções e badge de pendentes; no celular vira gaveta acionada por botão no topo. Item ativo com fundo `--muted`, barra primária e `aria-current="page"`.

## Responsividade

| Faixa | Comportamento |
| --- | --- |
| < 640 px | uma coluna; tabelas com rolagem horizontal e colunas secundárias ocultas; botões de ação com 44 px de altura |
| 640–1024 px | grade de produtos em 2 colunas; barra lateral como gaveta |
| ≥ 1024 px | barra lateral fixa; grade de produtos em 3 colunas; fila da cozinha em 3–4 colunas |

## Acessibilidade

- Contraste mínimo 4,5:1 para texto e 3:1 para ícones/bordas de controles (tokens acima verificados).
- Foco sempre visível (`focus-visible` com anel de 2 px); ordem de tabulação natural; link “Pular para o conteúdo”.
- Componentes Radix fornecem papéis ARIA, gerenciamento de foco e teclado em diálogos, menus, selects e abas.
- Ícones decorativos com `aria-hidden`; botões só com ícone têm `aria-label`.
- Mensagens de erro de formulário anunciadas (`role="alert"` no resumo, `aria-invalid` nos campos).
- Respeita `prefers-reduced-motion` (animações desativadas).
- Idioma da página `pt-BR`; datas e moeda formatadas com `Intl` em `pt-BR`.
