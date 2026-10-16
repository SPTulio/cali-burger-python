import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { useCart } from "@/features/cart/store";
import type { Role, User } from "@/types/api";

export const HOME_BY_ROLE: Record<Role, string> = {
  customer: "/",
  manager: "/painel/pedidos",
  cook: "/cozinha",
};

/** Usuário logado (null = visitante). A sessão vive em cookie HttpOnly no servidor. */
export function useSession() {
  return useQuery({
    queryKey: queryKeys.session,
    queryFn: async (): Promise<User | null> => {
      try {
        return (await authApi.me()).user;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    staleTime: 5 * 60_000,
  });
}

export function useSetSession() {
  const queryClient = useQueryClient();
  return (user: User | null) => {
    // Troca de usuário: descarta tudo o que foi carregado com a sessão anterior.
    queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== "session" });
    queryClient.setQueryData(queryKeys.session, user);
  };
}

export function useLogout() {
  const clearCart = useCart((s) => s.clear);
  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      clearCart();
      // Recarrega no login: descarta todo o estado em memória da sessão anterior e evita
      // que o guard da página atual mande para o login com "?next=" da área que foi deixada.
      window.location.replace("/entrar");
    },
  });
}

/** Destino seguro após o login: só caminhos internos do próprio site. */
export function safeNext(next: string | null, role: Role): string {
  if (next && next.startsWith("/") && !next.startsWith("//")) {
    const isStaffArea = next.startsWith("/painel") || next.startsWith("/cozinha");
    if ((role === "customer") !== isStaffArea) return next;
  }
  return HOME_BY_ROLE[role];
}
