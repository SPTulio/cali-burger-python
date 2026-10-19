import { Info } from "lucide-react";
import type { ReactNode } from "react";

import { formatDate } from "@/lib/format";

/** Mesma versão registrada no aceite do cadastro (backend: PRIVACY_POLICY_VERSION). */
export const PRIVACY_POLICY_VERSION = "2026-10-19";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="flex flex-col gap-2 text-[15px] leading-relaxed text-muted-foreground [&_strong]:text-foreground">
        {children}
      </div>
    </section>
  );
}

export function PrivacyPage() {
  return (
    <article className="mx-auto flex max-w-3xl flex-col gap-8 pb-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Política de Privacidade</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Versão de {formatDate(PRIVACY_POLICY_VERSION, "long")}
        </p>
        <div className="mt-4 flex gap-2 rounded-md border border-dashed bg-muted/40 p-3 text-sm text-muted-foreground">
          <Info className="mt-0.5 size-4 shrink-0 text-info" aria-hidden />
          <p>
            O Cali Burger é um projeto de portfólio com dados fictícios. Este texto descreve como o
            sistema trata dados pessoais e serve de modelo; antes de uso real, deve ser revisado
            por assessoria jurídica e completado com os dados do controlador.
          </p>
        </div>
      </header>

      <Section title="1. Quem trata os seus dados">
        <p>
          A lanchonete Cali Burger é a <strong>controladora</strong> dos dados informados no
          cadastro e nos pedidos, nos termos da Lei Geral de Proteção de Dados (Lei nº
          13.709/2018 — LGPD). Contato do encarregado: privacidade@caliburger.example.
        </p>
      </Section>

      <Section title="2. Quais dados coletamos">
        <p>
          <strong>Cadastro:</strong> usuário, nome, e-mail, CPF, data de nascimento e endereço de
          entrega. <strong>Pedidos:</strong> itens, observações, valores, endereço usado na
          entrega e o histórico de status. <strong>Acesso:</strong> endereço IP e navegador
          associados à sessão, usados para segurança.
        </p>
        <p>
          Não coletamos dados de cartão: o pagamento é PIX (nesta demonstração, simulado).
        </p>
      </Section>

      <Section title="3. Para que usamos e com qual base legal">
        <p>
          <strong>Preparar e entregar pedidos</strong> — execução do contrato (art. 7º, V).{" "}
          <strong>Emitir documentos fiscais e cumprir obrigações legais</strong> — obrigação legal
          (art. 7º, II), o que inclui guardar o histórico de vendas.{" "}
          <strong>Proteger contas</strong> (limite de tentativas de login, sessões) — legítimo
          interesse (art. 7º, IX).
        </p>
        <p>
          Não usamos seus dados para publicidade nem os vendemos. Se um dia houver comunicações de
          marketing, elas dependerão do seu consentimento específico, que poderá ser revogado.
        </p>
      </Section>

      <Section title="4. Com quem compartilhamos">
        <p>
          Com a equipe da loja que prepara e entrega o pedido e com provedores de hospedagem e
          infraestrutura que operam o sistema, sempre no limite do necessário.
        </p>
      </Section>

      <Section title="5. Cookies e armazenamento no navegador">
        <p>
          Usamos apenas cookies <strong>essenciais</strong>: <code>cb_session</code> (sessão,
          inacessível a scripts) e <code>cb_csrf</code> (proteção contra requisições forjadas). O
          carrinho e a preferência de tema ficam no armazenamento local do seu navegador. Não há
          cookies de rastreamento ou de publicidade.
        </p>
      </Section>

      <Section title="6. Por quanto tempo guardamos">
        <p>
          Dados de cadastro: enquanto a conta existir. Ao excluir a conta, os dados pessoais são
          apagados; os pedidos permanecem no histórico de vendas apenas com o nome informado na
          época, pelo prazo exigido pela legislação fiscal. Sessões expiram após inatividade.
        </p>
      </Section>

      <Section title="7. Seus direitos">
        <p>
          Você pode confirmar o tratamento, acessar e corrigir seus dados (em “Meu perfil”),
          excluir sua conta (também em “Meu perfil”), pedir a portabilidade e informações sobre
          compartilhamento, e revogar consentimentos (art. 18 da LGPD), pelo contato do
          encarregado.
        </p>
      </Section>

      <Section title="8. Segurança">
        <p>
          Senhas são guardadas com hash bcrypt; a sessão usa cookie HttpOnly com proteção CSRF; o
          acesso a cada informação é restrito ao perfil necessário (cliente, balcão ou cozinha).
        </p>
      </Section>
    </article>
  );
}
