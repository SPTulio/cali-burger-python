import type { ReactNode } from "react";
import { Navigate, useLocation, useSearchParams } from "react-router";

import { ErrorState, FullPageSpinner } from "@/components/common";
import { HOME_BY_ROLE, safeNext, useSession } from "@/features/auth/session";
import type { Role } from "@/types/api";

/** Protege rotas por perfil. Visitante vai para o login (e volta depois); perfil errado vai
 *  para a área do próprio perfil. O backend confere tudo de novo a cada requisição. */
export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const session = useSession();
  const location = useLocation();

  if (session.isPending) return <FullPageSpinner />;
  if (session.isError) return <ErrorState error={session.error} onRetry={() => session.refetch()} />;
  if (!session.data) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/entrar?next=${next}`} replace />;
  }
  if (!roles.includes(session.data.role)) {
    return <Navigate to={HOME_BY_ROLE[session.data.role]} replace />;
  }
  return children;
}

/** Telas de login/cadastro: quem já está logado vai direto para a sua área. */
export function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const session = useSession();
  const [params] = useSearchParams();
  if (session.isPending) return <FullPageSpinner />;
  // Logo após o login também passa por aqui: respeita o destino pedido (?next=).
  if (session.data) return <Navigate to={safeNext(params.get("next"), session.data.role)} replace />;
  return children;
}
