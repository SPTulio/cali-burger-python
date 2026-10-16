import { Compass } from "lucide-react";
import { Link, useRouteError } from "react-router";

import { EmptyState, ErrorState } from "@/components/common";
import { Button } from "@/components/ui/button";

export function NotFound() {
  return (
    <EmptyState
      className="min-h-[60dvh]"
      icon={Compass}
      title="Página não encontrada"
      description="O endereço pode ter mudado ou não existe."
      action={
        <Button asChild>
          <Link to="/">Ir para o início</Link>
        </Button>
      }
    />
  );
}

export function RouteError() {
  const error = useRouteError();
  return (
    <div className="flex min-h-dvh items-center justify-center p-6">
      <ErrorState error={error} onRetry={() => window.location.reload()} />
    </div>
  );
}
