# 05 · Registro de decisões

Decisões técnicas e de produto tomadas durante a reconstrução, com o motivo de cada uma. Ambiguidades do sistema original estão em [01-auditoria.md §10](01-auditoria.md#10-dúvidas-e-comportamentos-não-confirmados).

## Arquitetura e stack

| # | Decisão | Motivo |
| --- | --- | --- |
| A1 | **FastAPI síncrono** (sem `async`) | O domínio é transacional com travas de linha (`SELECT … FOR UPDATE`). Endpoints síncronos rodam no threadpool e mantêm o código de transação simples; não há I/O concorrente que justifique um driver assíncrono. |
| A2 | **SQLAlchemy 2 ORM + Alembic**, migrações revisadas manualmente | Tipagem (`Mapped[...]`), consultas parametrizadas por padrão e histórico versionado do esquema. Um teste garante que modelos e migrações não divergem. |
| A3 | **Sessão no servidor** (token opaco em cookie HttpOnly) em vez de JWT | Permite revogar sessões (logout, troca de senha, exclusão de conta) e não expõe tokens ao JavaScript. O banco guarda só o SHA-256 do token. |
| A4 | **CSRF por token sincronizado** (cookie legível + cabeçalho `X-CSRF-Token`, hash guardado na sessão) | Necessário com autenticação por cookie. SameSite=Lax reduz o risco, o token fecha o restante. |
| A5 | **bcrypt** (custo 12) | Compatível com os hashes `$2y$` gerados pelo PHP: as senhas dos usuários existentes continuam válidas após a importação. |
| A6 | **React Query** para dados do servidor e **Zustand** só para o carrinho | O estado vindo da API fica em cache com invalidação por domínio; o carrinho é o único estado de cliente que precisa persistir (no navegador, como a sessão do original). |
| A7 | Componentes no estilo **shadcn/ui** escritos no repositório (Radix + Tailwind) | Acessibilidade de diálogos, menus e abas resolvida pelo Radix, com visual próprio e sem depender de um gerador externo. |
| A8 | **Select nativo** estilizado nos formulários | Listas curtas; o seletor nativo é mais acessível e usa o seletor do próprio celular. |
| A9 | **Telas da equipe carregadas sob demanda** (lazy routes) | O cliente não baixa o código do painel. |
| A10 | Gráfico de faturamento em **SVG próprio** | Uma única série de colunas; uma biblioteca de gráficos adicionaria ~100 kB sem necessidade. Cor validada para contraste e luminosidade nos dois temas. |

## Modelo de dados

| # | Decisão | Motivo |
| --- | --- | --- |
| M1 | Tabela única `users` com `role` | Clientes, balconistas e cozinheiros tinham tabelas duplicadas. Unificar simplifica autenticação, sessões e auditoria. |
| M2 | `UNIQUE(cpf, account_type)` com coluna gerada (`customer`/`staff`) | Preserva as regras originais: CPF único entre clientes e entre funcionários, mas uma mesma pessoa pode ser cliente e funcionária. |
| M3 | Funcionários identificados por **id**, nunca pelo CPF em URLs | CPF é dado pessoal; o original usava o CPF como chave e em formulários. |
| M4 | Status em **enum técnico** e `cancelled` ≠ `rejected` | O original misturava cancelamento do cliente e recusa da loja em um texto único. Ambos continuam fora do relatório e devolvem o estoque. |
| M5 | `order_status_events` (linha do tempo) | Mostra ao cliente quando cada etapa aconteceu e registra quem aceitou/enviou. Não altera regras. |
| M6 | `orders.delivery_address` congelado | O pedido mostra para onde foi entregue mesmo que o cliente mude o endereço depois. |
| M7 | `order_items.unit_price` além do subtotal | Facilita relatórios e a exibição do pedido sem recalcular. |
| M8 | `payments` sem `customer_id` | Redundante com o pedido (normalização). |
| M9 | Datas em **UTC** no banco; dias do relatório no fuso `TIMEZONE` | O original dependia do fuso do servidor PHP. Limitação: o deslocamento do fuso é calculado no momento da consulta — correto para `America/Sao_Paulo` (sem horário de verão desde 2019); fusos com horário de verão teriam desvio de 1 h nos dias de transição. |
| M10 | Categorias como dado de referência criado pela migração | Não havia tela de gestão no original (D04). |

## Experiência do usuário

| # | Decisão | Motivo |
| --- | --- | --- |
| U1 | Login único (usuário **ou** CPF) | Substitui três telas de login sem mudar a regra: clientes entram pelo usuário, funcionários pelo CPF. |
| U2 | Cadastro já entra na conta | Remove um passo (o original voltava para o login). |
| U3 | Botões +/− e carrinho lateral | O original exigia digitar quantidades em todos os itens e enviar o formulário. Limite de 20 por item e o limite do estoque continuam valendo. |
| U4 | Filtros na URL (status, datas, busca, página) | Voltar do detalhe mantém o contexto; links podem ser compartilhados. |
| U5 | Atualização automática sem recarregar (cozinha 15 s, pendentes 20 s, “meus pedidos” 30 s) | O original recarregava a página inteira a cada 30 s na cozinha. |
| U6 | Excluir conta exige a senha | Proteção extra para ação irreversível (o original pedia só confirmação). |
| U7 | Chave de idempotência por conteúdo do carrinho | Duplo clique ou reenvio por rede instável não criam pedido duplicado. |
| U8 | Fila “Aguardando aceitação” do mais antigo para o mais novo | Ordem de atendimento; a aba “Todos os pedidos” continua do mais novo para o mais antigo, como no original. |
| U9 | Tema claro e escuro | Mesmos tokens semânticos; o escuro tem passos próprios, não uma inversão automática. |

## Fase 1 do roteiro (evolução)

| # | Decisão | Motivo |
| --- | --- | --- |
| E1 | **Cozinha marca “Pronto”, balcão despacha** | Separa “terminou o preparo” de “saiu da loja”: dá o tempo real de preparo (base da previsão) e quem entrega o pedido é o balcão. Muda a regra original (o cozinheiro enviava). |
| E2 | Horários em **intervalos por dia da semana** no fuso da loja; `fecha ≤ abre` vira a meia-noite; sem horários = sempre aberta | Cobre almoço + jantar e madrugada sem tabela de exceções; um banco recém-criado continua funcionando como o original (sem horário). |
| E3 | Fechada/pausada **bloqueia no servidor** (`store_closed`, `store_paused`), não só na tela | Um carrinho aberto antes do fechamento não consegue finalizar. |
| E4 | Pausa de item separada do estoque | “Acabou o pão de brioche hoje” não deve exigir zerar ingredientes nem apagar a receita. |
| E5 | Taxa **por nome de bairro** (comparado sem acento e sem diferenciar maiúsculas), com taxa padrão opcional | O cadastro já tem bairro; distância exigiria geocodificação externa. Sem bairros e sem taxa padrão, a entrega é grátis para todos — o comportamento original. |
| E6 | Taxa e previsão **congeladas no pedido** (`subtotal`, `delivery_fee`, `eta_*`) | O cliente vê o que aceitou, mesmo que a loja mude a taxa depois. O relatório continua somando o `total`. |
| E7 | Previsão = preparo médio (últimos 14 dias, mínimo 5 pedidos; senão o tempo configurado) + fila + deslocamento do bairro, em uma janela de 10 min arredondada para 5 | Estimativa simples e explicável, que melhora sozinha com o histórico, sem prometer horário exato. |
| E8 | Motivo **obrigatório** na recusa e opcional no cancelamento, guardado no evento da linha do tempo | O cliente entende por que o pedido foi recusado; a recusa é uma ação da loja que precisa de justificativa. |
| E9 | “Peça de novo” **no navegador**, reaproveitando o carrinho | Não há endpoint novo: o pedido antigo é cruzado com o cardápio atual; itens pausados, esgotados ou removidos ficam de fora com aviso, e a quantidade respeita o estoque. |
| E10 | Aceite da política **versionado** (`privacy_version`, `privacy_accepted_at`) | Permite pedir novo aceite quando o texto mudar. Usuários importados ou de demonstração ficam sem aceite registrado. |

## Segurança

- Limite de tentativas de login persistido no banco por **IP + identificador** (o original contava por sessão PHP, contornável descartando o cookie).
- Troca de senha encerra as **outras** sessões; exclusão de conta encerra todas.
- Upload verificado pelo conteúdo real (Pillow), tamanho e dimensões máximos, nome aleatório; a imagem antiga é apagada ao substituir ou excluir o item.
- Erros 500 nunca expõem detalhes (registrados no log com `request_id`); logs não incluem corpo de requisição, senhas nem tokens.
- Cabeçalhos `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` na API e CSP no Nginx.
- Pedido de outro cliente responde **404** (não revela que o número existe).

## Limitações conhecidas

- Pagamento PIX é **simulado** (como no original) e identificado assim na interface.
- Sem notificações em tempo real (WebSocket/SSE): as telas fazem polling com intervalos curtos.
- A taxa de entrega depende do bairro digitado pelo cliente; um nome escrito de outro jeito (abreviação, erro de digitação) cai na taxa padrão ou fica fora da área.
- A Política de Privacidade é um modelo para portfólio e precisa de revisão jurídica antes de uso real.
- O workflow de CI roda no GitHub Actions (testes do backend com MySQL 8.4; lint, testes Vitest, tipos e build do frontend). O **Docker Compose** foi escrito e validado sintaticamente, mas não pôde ser executado no ambiente de desenvolvimento usado (sem Docker); a aplicação foi executada e testada localmente com MySQL 8.4.
- O frontend tem testes unitários e de componente (Vitest + Testing Library em jsdom), mas não testes ponta a ponta no navegador: os fluxos completos das telas foram verificados manualmente.
