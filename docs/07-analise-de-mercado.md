# 07 · Análise de mercado e sugestões de evolução

Comparação do Cali Burger com produtos reais de pedidos de comida: marketplaces (iFood, Uber Eats, DoorDash), plataformas de canal próprio usadas no Brasil (Goomer, Anota AI, Cardápio Web, Saipos), apps de redes de hamburgueria (McDonald's, Burger King) e sistemas de cozinha (Toast, Square). Pesquisa feita em outubro de 2026.

> **Qualidade das evidências.** Os dados de mercado mais confiáveis aqui são a pesquisa da Abrasel (2.176 estabelecimentos) e o benchmark de UX da Baymard Institute (8 grandes sites e apps de delivery, 390+ parâmetros). Números de aumento de ticket ou conversão (“+20% com combos”, “+30% com PWA”) vêm quase sempre de **fornecedores** e não foram verificados em estudo independente; estão marcados como *alegação de fornecedor*. Pontos jurídicos (CDC, LGPD, alérgenos) são orientação geral e precisam de validação com um profissional antes de virarem regra no produto.

---

## 1. Resumo executivo

O Cali Burger já cobre bem o **núcleo** de um sistema de pedidos: cardápio com disponibilidade pelo estoque, pedido transacional, máquina de estados, fila da cozinha, relatório e equipe — com qualidade técnica acima da média (testes, segurança, acessibilidade). O que o separa de um produto comercial está em quatro frentes:

| # | Mudança | Por quê | Esforço |
| --- | --- | --- | --- |
| 1 | **Complementos e opções por item** (ponto da carne, adicionais pagos, “escolha 1”) | É a forma padrão de personalizar lanche em todas as referências; hoje só existe observação em texto livre, que a cozinha precisa interpretar e que não cobra adicional | G |
| 2 | **Entrega de verdade**: taxa por bairro/raio, área atendida, tempo estimado e **retirada no balcão** | Toda referência mostra taxa e prazo antes do pagamento; a Baymard aponta prazo sem detalhe como motivo de desistência | M |
| 3 | **Horário de funcionamento e “pausar loja/item”** | Hoje a loja aceita pedido 24 h; pausar um item só é possível zerando o estoque | P |
| 4 | **“Peça de novo” na página inicial** | Recompra é o comportamento central em delivery e a falha mais citada pela Baymard | P |
| 5 | **Avisos ativos ao cliente** (WhatsApp/push) com previsão de entrega | WhatsApp responde por 26% do faturamento de delivery no Brasil; acompanhamento reduz ansiedade (caso Domino's) | M |
| 6 | **Motivo de recusa/cancelamento** e reembolso | Recusa sem motivo é ruim para o cliente e frágil diante do CDC | P |
| 7 | **KDS mais completo**: cronômetro com cores, “pronto” separado de “saiu para entrega”, desfazer | Padrão de Toast e similares; hoje a cozinha tem um único botão | M |
| 8 | **Estoque com unidade de medida, custo e mínimo por ingrediente → CMV** | Saipos e concorrentes vendem “CMV a cada venda”; hoje o estoque é só contagem com limite global | M |
| 9 | **Cupons e fidelidade** (com consentimento LGPD) | Presente em Goomer, Anota AI, McDonald's e Burger King | M |
| 10 | **PIX real** (QR dinâmico, expiração, webhook + conciliação) | Necessário para operar de verdade; hoje é simulado | M |

Esforço: P = dias, M = 1–2 semanas, G = 3+ semanas (estimativas para uma pessoa, com testes).

---

## 2. Panorama do mercado (Brasil)

- **Onde está o faturamento de delivery** (Abrasel, 2025): marketplaces **54%**, WhatsApp **26%**, site/app próprio **12%** (presente em 39% dos estabelecimentos), telefone **8%**. 63% dos estabelecimentos usam WhatsApp no delivery e **38%** já automatizam o atendimento nele. → O Cali Burger compete no segmento de **canal próprio**, cujo valor está em fugir da comissão do marketplace, ter os dados do cliente e fidelizar.
- **Plataformas de canal próprio** (Goomer, Anota AI, Cardápio Web) cobram mensalidade e oferecem um pacote parecido: cardápio por link/QR Code, complementos e combos, cupons, cashback/fidelidade, pedido pelo WhatsApp com atendente virtual, agendamento, pagamentos (Pix, cartão, carteiras), relatórios e integração com PDV/KDS. A Anota AI destaca “**Peça também**” (sugestão no carrinho), “**Peça de novo**” (repetir o último pedido em um toque) e **recuperação de carrinho abandonado**.
- **Redes de hamburgueria** (McDonald's, Burger King) investem em app próprio com **pontos/fidelidade** (Meu Méqui: 100 pontos por R$ 1, validade de 6 meses), **cupons**, **peça e retire** e **informação nutricional**.
- **UX de referência** (Baymard 2026, 8 sites incluindo McDonald's, Burger King, KFC, Domino's, iFood-like DoorDash/Uber Eats): **nenhum** chegou a nível “decente”. Os problemas recorrentes são justamente oportunidades: recompra pouco apoiada, ausência de filtros e informação para restrições alimentares, falta de caminhos de volta/orientação e prazo de entrega sem detalhe suficiente.

---

## 3. Comparativo de funcionalidades

✅ tem · ◐ parcial · ❌ não tem

| Recurso | Cali Burger hoje | Marketplace (iFood/Uber Eats) | Canal próprio (Goomer/Anota AI) | Apps de rede (McDonald's/BK) |
| --- | :-: | :-: | :-: | :-: |
| Cardápio por categoria com fotos | ✅ | ✅ | ✅ | ✅ |
| Disponibilidade pelo estoque (receita) | ✅ | ◐ | ◐ | ◐ |
| Complementos / opções obrigatórias | ❌ (só observação) | ✅ | ✅ | ✅ |
| Combos / promoções | ❌ | ✅ | ✅ | ✅ |
| Busca e filtros (vegetariano, sem glúten) | ❌ | ✅ | ◐ (selos) | ◐ |
| Informação nutricional / alérgenos | ❌ | ◐ | ◐ | ✅ |
| Taxa de entrega e área atendida | ❌ | ✅ | ✅ | ✅ |
| Tempo estimado de entrega | ❌ | ✅ | ◐ | ✅ |
| Retirada no balcão | ❌ | ✅ | ✅ | ✅ |
| Agendamento | ❌ | ◐ | ✅ | ❌ |
| Horário de funcionamento / loja fechada | ❌ | ✅ | ✅ | ✅ |
| Pagamento real (Pix/cartão) | ❌ (simulado) | ✅ | ✅ | ✅ |
| Cupons | ❌ | ✅ | ✅ | ✅ |
| Fidelidade / cashback | ❌ | ◐ | ✅ | ✅ |
| Acompanhamento do pedido | ✅ (linha do tempo) | ✅ (+ mapa) | ✅ | ✅ |
| Avisos ativos (WhatsApp/push) | ❌ | ✅ | ✅ | ✅ |
| Repetir pedido | ❌ | ✅ | ✅ | ◐ |
| Avaliação do pedido | ❌ | ✅ | ✅ | ◐ |
| Fila da cozinha (KDS) | ◐ | — | ✅ (integração) | ✅ |
| Estoque por ficha técnica | ✅ | ❌ | ◐ | — |
| CMV / custo por prato | ❌ | ❌ | ◐ | — |
| Relatórios | ◐ | ✅ | ✅ | — |
| Proteção contra pedido duplicado, concorrência de estoque | ✅ | ✅ | ? | ? |

**Onde o Cali Burger já está à frente** de soluções simples de canal próprio: baixa de estoque transacional por receita com trava contra venda dupla, linha do tempo auditável, idempotência no pagamento, controle de acesso por perfil testado e acessibilidade (teclado, contraste, leitor de tela).

---

## 4. Sugestões detalhadas

Cada item traz **o que as referências fazem**, **como está hoje** e **o que mudar**. Prioridade: 🔴 alta · 🟠 média · 🟢 baixa.

### 4.1 Cardápio e produto

1. 🔴 **Complementos e grupos de opções** — *Referências:* Toast, Square, DoorDash e OrderOut modelam “grupos de modificadores” com regras de mínimo/máximo (“escolha 1”, “até 3”), obrigatórios ou opcionais; adicionais podem ter preço. *Hoje:* só observação livre (“sem cebola”), sem preço e sem efeito no estoque. *Mudança:* tabelas `option_groups` (nome, min, max, obrigatório) e `options` (nome, preço extra, **receita própria** para baixar estoque — ex.: “bacon extra” consome 2 fatias); tela do item em modal/página com grupos, preço recalculado ao vivo e validação antes de adicionar. Manter a observação livre como complemento. Afeta: pedido (itens com opções congeladas), cozinha (mostrar opções destacadas), relatório (adicionais mais vendidos).
2. 🔴 **Editar item no carrinho** — A Baymard cita o carrinho do Chipotle (“Editar” por item) como modelo e relata usuários apagando e refazendo itens. *Hoje:* dá para mudar quantidade e observação; com complementos, será preciso “editar” reabrindo o item.
3. 🟠 **Combos e promoções** — Presentes em todas as referências. Modelo simples: combo = item com grupos obrigatórios (lanche + acompanhamento + bebida) e preço próprio; promoções por período. *Alegação de fornecedor:* aumento de 20–25% no ticket com ofertas.
4. 🟠 **Selos e filtros alimentares** (vegetariano, sem lactose, sem glúten, picante) e **alérgenos** por item — A Baymard aponta a falta de caminho para restrições alimentares em **todos** os sites avaliados; a Anota AI oferece selos. Há leis/recomendações locais exigindo informação de alérgenos em cardápios (ex.: Ceará, Lei 17.899/2022). Implementar como atributos do item derivados da receita quando possível (ingrediente marcado como “contém glúten/leite”).
5. 🟠 **Busca no cardápio** e seção **“Mais pedidos”** (dados já existem no relatório).
6. 🟢 **Descrições melhores e fotos padronizadas** — O guia da Anota AI destaca fotos reais e descrições claras; um artigo cita estudo do *International Journal of Hospitality Management* com +27% de pedidos por descrições melhores (não verificado na fonte original).
7. 🟢 **Preço por horário** (happy hour) — oferecido pela Goomer; útil depois de combos.

### 4.2 Carrinho e checkout

8. 🔴 **Taxa de entrega e área atendida** — Sistemas como Alterdata e 99Food configuram **taxa padrão + taxa por bairro** ou **área circular/poligonal**, com **frete grátis acima de um valor**. A Saipos recomenda não passar de ~8 km (orientação de fornecedor). *Mudança:* cadastro de bairros/faixas de distância com taxa e tempo extra; checkout mostra subtotal, taxa e total **antes** do pagamento; endereço fora da área bloqueia com mensagem clara.
9. 🔴 **Tempo estimado antes de pagar** — A Baymard lista prazo de entrega sem detalhe como um dos pontos que impedem o usuário de concluir. *Mudança:* estimativa = tempo médio de preparo (calculável pela linha do tempo já gravada) + tempo da área + fila atual; exibir faixa (“40–55 min”) no checkout e no acompanhamento.
10. 🔴 **Retirada no balcão** — “Peça e Retire” é central em McDonald's e Burger King. Novo tipo de pedido sem taxa nem endereço, com status “Pronto para retirar”.
11. 🟠 **Formas de pagamento na entrega** (dinheiro com troco, cartão na maquininha) além do Pix — oferecidas pela Goomer. Útil enquanto não há gateway.
12. 🟠 **Pedido mínimo** — A Anota AI permite configurar. *Atenção:* há relatos de entendimento do Procon-RJ contra valor mínimo em plataformas (fonte de fórum, não oficial). Se adotado, deixar configurável e transparente, ou preferir “frete grátis acima de R$ X”.
13. 🟠 **Agendamento** — Goomer oferece. A Baymard recomenda **seletor de calendário/horários em grade** em vez de listas longas ou rolagens duplas, e indicar claramente a data escolhida.
14. 🟠 **Cupom de desconto** no checkout (primeira compra, influenciador, pós-venda — tipos citados pela Goomer).
15. 🟢 **CPF na nota** opcional no checkout (já temos o CPF do cliente; perguntar se deseja incluir).

### 4.3 Pagamento

16. 🔴 **Pix real** — Provedores (Asaas, Mercado Pago, etc.) geram **QR dinâmico com expiração**, permitem pagar uma única vez e notificam por **webhook**. *Mudança:* status de pagamento separado do status do pedido (`pending → paid → refunded/expired`); o pedido só entra na fila do balcão depois de pago; QR expira (ex.: 15 min) e devolve o estoque reservado; **conciliação periódica** além do webhook — a página de status da Asaas registra incidente que afetou geração e pagamento de QRs dinâmicos, então não dá para depender só do webhook.
17. 🟠 **Estorno** ao recusar/cancelar pedido pago (Pix devolução) com registro na linha do tempo.

### 4.4 Pós-compra e relacionamento

18. 🔴 **“Peça de novo”** — Baymard: usuários procuram a recompra na página inicial e os sites mostram anúncios; DoorDash (“Order Again”) é o exemplo positivo; Anota AI tem “Peça de novo” em um toque. *Mudança:* faixa “Seus pedidos recentes” no topo do cardápio para cliente logado e botão “Repetir” no histórico (recria o carrinho, avisando itens indisponíveis).
19. 🔴 **Avisos ativos** — Domino's criou o *Tracker* para reduzir a ansiedade da espera; o próprio desenvolvedor relata que o cliente vivia uma “montanha-russa emocional”. Hoje o Cali Burger só atualiza se a página estiver aberta. *Mudança:* notificar mudança de status por **WhatsApp** (API oficial do WhatsApp Business) e/ou **Web Push** (PWA); usar **SSE** em vez de polling nas telas abertas.
20. 🟠 **Avaliação do pedido** (nota + comentário após “Recebi”) — Goomer e marketplaces; alimenta um indicador de satisfação no painel.
21. 🟠 **Recuperação de carrinho abandonado** (cliente logado que não finalizou recebe lembrete) — Anota AI. Exige consentimento de comunicação (LGPD).
22. 🟢 **Instalar como app (PWA)** — manifesto + ícones + offline do cardápio. Benefícios citados em casos de fornecedores, sem dado independente.

### 4.5 Fidelização e marketing

23. 🟠 **Cashback ou pontos** — Meu Méqui (100 pontos por R$ 1, validade de 6 meses, resgate no app) e Clube BK (pontos pelo CPF). Para um negócio pequeno, **cashback em saldo** é mais simples de entender. Regras: crédito só após “Concluído”, estorno se cancelado, validade.
24. 🟠 **Consentimento separado para marketing** — Usar CPF/dados para fidelidade e promoções exige base legal própria (geralmente consentimento); dados para entrega e nota têm outras bases. Adicionar opção “Quero receber promoções” no cadastro e no perfil, revogável.
25. 🟢 **Banners/destaques** gerenciáveis no topo do cardápio (Anota AI oferece banners personalizados).

### 4.6 Operação do balcão

26. 🔴 **Horário de funcionamento e “loja fechada”** — Hoje a loja aceita pedidos a qualquer hora. *Mudança:* horários por dia da semana, exceções (feriados) e botão **“Pausar pedidos”**; vitrine mostra “Fechado — abre às 18h” e permite apenas agendar.
27. 🔴 **Pausar item** sem mexer no estoque (“indisponível hoje”).
28. 🔴 **Motivo obrigatório ao recusar** (sem ingrediente, fora da área, loja fechando…), exibido ao cliente; e **motivo no cancelamento** do cliente. Ajuda no atendimento e na conformidade com o CDC, que prevê abatimento ou cancelamento quando a entrega não corresponde à oferta (arts. 20, 30 e 35, segundo o Idec).
29. 🟠 **Alerta sonoro** de novo pedido e **aceite automático** opcional (Anota AI tem os dois).
30. 🟠 **Impressão de comanda** (ticket para cozinha/entregador) — CSS de impressão já resolve o básico.
31. 🟢 **Central de pedidos de vários canais** (integração com iFood) — diferencial das plataformas pagas; grande esforço, só se o negócio exigir.

### 4.7 Cozinha (KDS)

32. 🔴 **Cronômetro por pedido com cores por tempo** — Toast mostra um cronômetro no canto de cada ticket desde o envio à cozinha; outros KDS mudam a cor do ticket conforme o tempo passa. *Hoje:* há “X min”, com alerta único aos 20 min. *Mudança:* faixas configuráveis (verde/âmbar/vermelho) e ordenação por atraso.
33. 🔴 **Separar “Pronto” de “Saiu para entrega”** — Na maioria das operações, quem termina o lanche não é quem entrega. Novo status `ready` (pronto para retirada/entregador) antes de `out_for_delivery`; para retirada no balcão, `ready` encerra o fluxo com o cliente buscando.
34. 🟠 **Desfazer/recuperar** (recall) o último pedido marcado por engano — recurso padrão em KDS.
35. 🟠 **Visão agregada** (“12 Cali Clássico na fila”) e **modo tela cheia** para tablet na parede, com botões grandes.
36. 🟢 **Estações** (chapa, fritura, bebidas) — roteamento por estação como no Square; só faz sentido com mais volume.

### 4.8 Estoque e gestão

37. 🔴 **Unidade de medida e custo do insumo** (g, ml, un.; custo por unidade) → **custo do prato e CMV**. Saipos vende exatamente “CMV teórico e real a cada venda”. Com a receita que já existe, o CMV teórico sai quase de graça: soma do custo dos ingredientes × quantidade.
38. 🔴 **Estoque mínimo por ingrediente** (substitui o limite global de 10, que não serve para “pão” e “sachê de ketchup” ao mesmo tempo) e **lista de compras** sugerida.
39. 🟠 **Movimentações de estoque auditáveis** (entrada, ajuste com motivo, perda, consumo de pedido, devolução) em vez de sobrescrever a quantidade — essencial para entender divergências.
40. 🟢 **Fornecedores e ordens de compra** — só em fase posterior.

### 4.9 Relatórios

41. 🟠 **Comparativo com o período anterior** nos indicadores (↑/↓ %).
42. 🟠 **Horários de pico** e **dia da semana** (Goomer destaca “horários de pico”).
43. 🟠 **Tempos operacionais** a partir da linha do tempo já gravada: aceite, preparo, entrega e total; **taxa de recusa/cancelamento** e motivos.
44. 🟠 **Margem por produto** (com o CMV do item 37).
45. 🟢 **Exportar CSV/Excel** de pedidos e vendas (critério de “propriedade dos dados” citado pela Anota AI na escolha de plataforma).

### 4.10 Design e UX geral

46. 🟠 **Página inicial com contexto da loja**: status aberto/fechado, tempo médio de entrega, taxa a partir de, área atendida — informação que o cliente procura antes de escolher.
47. 🟠 **Caminhos de volta e orientação** — A Baymard aponta ausência de breadcrumbs/caminhos de volta como falha generalizada. No Cali Burger, o detalhe do pedido e o formulário de item já têm “Voltar”; padronizar em todas as páginas profundas e preservar estado ao voltar (já feito com filtros na URL).
48. 🟠 **Página/modal de produto** com foto grande, descrição completa, informação nutricional e complementos (necessário para o item 1).
49. 🟢 **Microinterações moderadas**: animação curta do contador do carrinho ao adicionar, confirmação visual na mudança de status (respeitando `prefers-reduced-motion`, que já é tratado).
50. 🟢 **Identidade**: fotografia consistente (mesmo fundo/ângulo), ilustração para estados vazios; o design system atual comporta sem mudanças estruturais.

### 4.11 Legal e confiança

51. 🔴 **Política de privacidade e termos** acessíveis no rodapé e no cadastro; registro do aceite (versão + data).
52. 🟠 **Direitos do titular (LGPD)**: além da exclusão (já existe), **exportar meus dados** e informar com quem são compartilhados (ex.: entregadores, gateway).
53. 🟠 **Informação ao consumidor** no checkout: política de cancelamento (hoje: só enquanto aguarda aceite), prazo e canal de atendimento.
54. 🟢 **Nota fiscal (NFC-e)** — obrigatória na operação real; normalmente via integração com emissor/PDV. Fora do escopo do portfólio, mas vale mencionar.

### 4.12 Plataforma e técnica

55. 🟠 **Tempo real com SSE/WebSocket** no lugar do polling (cozinha, balcão, acompanhamento).
56. 🟠 **Testes ponta a ponta** (Playwright) dos fluxos críticos no CI — o projeto já usa Playwright para as capturas.
57. 🟢 **Observabilidade**: métricas (pedidos/min, erros), rastreamento por `request_id` (já gerado) em uma ferramenta de logs.
58. 🟢 **Multi-loja** (várias unidades com estoque e horários próprios) — só se a proposta crescer.

---

## 5. Roteiro sugerido

**Fase 1 — Pronto para operar (2–3 semanas)**
Horário de funcionamento + pausar loja/item (26, 27) · motivo de recusa/cancelamento (28) · “Peça de novo” (18) · retirada no balcão (10) · status “Pronto” na cozinha e cronômetro com cores (32, 33) · taxa por bairro + tempo estimado (8, 9) · política de privacidade (51).

**Fase 2 — Ticket médio e fidelização (3–5 semanas)**
Complementos e grupos de opções com receita (1, 2, 48) · combos (3) · cupons (14) · selos/alérgenos e busca (4, 5) · avaliação (20) · consentimento de marketing (24) · SSE (55).

**Fase 3 — Pagamento e gestão (3–4 semanas)**
Pix real com webhook, expiração e conciliação (16, 17) · unidade/custo/CMV e mínimo por ingrediente (37, 38) · movimentações de estoque (39) · relatórios de tempos, picos, margem e comparação (41–44) · avisos por WhatsApp/push (19).

**Fase 4 — Crescimento**
Cashback (23) · PWA (22) · carrinho abandonado (21) · agendamento (13) · integração com marketplace (31) · multi-loja (58).

---

## 6. O que manter

- **Baixa de estoque transacional por receita** e trava contra venda dupla — poucos sistemas de canal próprio fazem isso direito; é um diferencial real.
- **Linha do tempo auditável** do pedido — base para tempos médios, estimativas e relatórios operacionais.
- **Máquina de estados no servidor** e permissões por perfil — facilita adicionar `ready`, retirada e pagamento real sem quebrar regras.
- **Design sóbrio e funcional** (tabelas no balcão, tickets na cozinha, fotos só na vitrine) — alinhado ao que a Baymard aponta como prioridade: clareza e caminhos previsíveis acima de ornamentos.

---

## Fontes

- Abrasel — [WhatsApp representa 26% do faturamento com delivery](https://abrasel.com.br/noticias/noticias/whatsapp-representa-26-do-faturamento-delivery-bares-restaurantes/) · [Mobile Time](https://www.mobiletime.com.br/noticias/14/03/2025/whatsapp-bar-restaurante/)
- Baymard Institute — [Food Delivery & Takeout UX Benchmark 2026](https://baymard.com/research-articles/food-delivery-and-takeout-ux-benchmark-2026) · [3 High-Level UX Takeaways](https://baymard.com/blog/food-delivery-takeout-launch) · [Past purchases on the homepage](https://baymard.com/blog/grocery-food-delivery-orders) · [Food delivery research](https://baymard.com/research/online-food-delivery)
- Plataformas de canal próprio — [Goomer](https://goomer.com.br/) · [Anota AI: melhor cardápio digital](https://anota.ai/blog/melhor-cardapio-digital-para-restaurante/) · [Anota AI vs Goomer](https://anota.ai/blog/goomer/) · [Rei do Delivery: Goomer ou Anota AI](https://reidodelivery.com.br/blog/goomer-ou-anota-ai) · [Rei do Delivery: sistemas de cardápio digital](https://reidodelivery.com.br/blog/melhores-sistemas-de-cardapio-digital) · [Saipos](https://saipos.com/sistema/restaurante)
- Entrega e taxas — [Alterdata: configuração de delivery](https://ajuda.alterdata.com.br/shopbase/delivery-shop-configuracao-97787507.html) · [99Food: entrega feita pela loja](https://99app.com/99food/restaurantes/guias/como-configurar-a-entrega-feita-pela-loja/) · [Saipos: como calcular frete](https://saipos.com/delivery/como-calcular-frete-delivery) · [Fórum Tecnoblog: Procon e valor mínimo](https://tecnoblog.net/comunidade/t/ifood-e-ze-delivery-sao-notificados-pelo-procon-por-valor-minimo-em-pedidos/59551)
- Apps de rede — [McDonald's (App Store)](https://apps.apple.com/BR/app/id1114009187) · [TecMundo: Meu Méqui](https://www.tecmundo.com.br/mercado/273796-meu-mequi-mcdonalds-lanca-programa-fidelidade-100-digital.htm) · [Mercado & Consumo: Méqui Sem Fila](https://mercadoeconsumo.com.br/05/08/2020/foodservice/mcdonalds-lanca-recurso-mequi-sem-fila-em-seu-aplicativo/) · [Burger King Brasil (App Store)](https://apps.apple.com/BR/app/id1295116265)
- Cozinha — [Toast: ticket times](https://doc.toasttab.com/doc/platformguide/adminInterpretingTicketTimes.html) · [EZ SoftPOS: KDS](https://help.ezsoftpos.com/support/solutions/articles/44002540120-kitchen-display-system-kds-) · [Square Community: Bump KDS](https://community.squareup.com/t5/Food-Beverage/Bump-Kitchen-Display-System-KDS-for-Square/m-p/330039)
- Complementos — [Toast: modifier groups](https://intercom.help/toast-central/en/articles/9307419-add-modifier-groups-and-modifiers-in-the-menu-builder) · [OrderOut: modifier groups](https://community.orderout.co/t/how-to-add-and-manage-modifier-groups-on-your-orderout-dashboard/85) · [Square: item modifiers](https://squareup.com/help/us/en/article/5119-create-and-manage-item-options) · [DoorDash: modifiers](https://merchants.doordash.com/en-us/learning-center/modifiers) · [Zuppler (alegação de fornecedor)](https://www.zuppler.com/blog/2025/2/28/boost-conversions-by-30-with-these-essential-menu-features) · [MenuTiger](https://www.menutiger.com/blog/choices-and-add-ons-to-your-online-menu) · [HungerRush](https://www.hungerrush.com/restaurant-operations/restaurant-upselling-the-art-and-science-of-an-enhanced-guest-experience/)
- Acompanhamento — [NPR: how a pizza app changed our relationship with waiting](https://www.npr.org/2026/09/18/nx-s1-5896338/how-a-pizza-app-changed-our-relationship-with-waiting) · [Restaurant Dive: Domino's tracker update](https://www.restaurantdive.com/news/dominos-tracker-update-artificial-intelligence-real-time-order-status/815556/) · [QSR Magazine: is your pizza tracker telling the truth](https://www.qsrmagazine.com/story/is-your-pizza-tracker-telling-the-truth/)
- Pix — [Asaas: cobranças via Pix](https://docs.asaas.com/docs/cobrancas-via-pix) · [QI Tech: webhook de QR expirado](https://docs.qitech.com.br/en/documentation/pix/webhook_por_qr_code_expirado) · [Asaas: incidente em QR dinâmico](https://isdown.app/status/asaas/incidents/646473-indisponibilidade-na-geracao-de-qrcodes-dinamicos-pix)
- Legal — [Consumidor Moderno: direitos no delivery](https://consumidormoderno.com.br/quais-direitos-consumidor-delivery/) · [MPCE: alérgenos em cardápios](https://mpce.mp.br/decon-alerta-que-cardapios-de-estabelecimentos-comerciais-de-sobral-devem-conter-informacoes-sobre-produtos-que-causam-alergias/) · [PrivacyTools: LGPD para restaurantes](https://www.privacytools.com.br/en/lgpd-para-restaurantes/) · [Nuvemshop: direitos LGPD](https://atendimento.nuvemshop.com.br/852458-quais-sao-os-direitos-que-a-lgpd-preve-para-os-consumidores-da-minha-loja)
