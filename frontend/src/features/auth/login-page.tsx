import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Eye, EyeOff, Info } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { z } from "zod";

import { errorMessage } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { AuthLayout } from "@/app/layouts";
import { Button } from "@/components/ui/button";
import { Field, FormError, Input } from "@/components/ui/field";
import { useSetSession } from "@/features/auth/session";

const schema = z.object({
  identifier: z.string().trim().min(1, "Informe seu usuário ou CPF."),
  password: z.string().min(1, "Informe sua senha."),
});
type LoginForm = z.infer<typeof schema>;

// Contas criadas pelo script de demonstração (backend/scripts/seed_demo.py).
const DEMO_ACCOUNTS = [
  { label: "Cliente", identifier: "joao" },
  { label: "Balconista / dono", identifier: "352.658.110-01" },
  { label: "Cozinheiro", identifier: "211.996.250-27" },
];
const DEMO_PASSWORD = "cali1234";
const SHOW_DEMO = import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === "true";

export function LoginPage() {
  const setSession = useSetSession();
  const [showPassword, setShowPassword] = useState(false);
  const form = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: { identifier: "", password: "" },
  });
  const { errors } = form.formState;

  const login = useMutation({
    mutationFn: (data: LoginForm) => authApi.login(data.identifier, data.password),
    // O guard RedirectIfAuthenticated leva ao destino (?next=) assim que a sessão muda.
    onSuccess: ({ user }) => setSession(user),
  });

  return (
    <AuthLayout>
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold tracking-tight">Entrar</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Acompanhe seus pedidos ou acesse o painel da equipe.
        </p>

        <form
          className="mt-8 flex flex-col gap-4"
          onSubmit={form.handleSubmit((data) => login.mutate(data))}
          noValidate
        >
          <FormError message={login.isError ? errorMessage(login.error) : null} />
          <Field
            label="Usuário ou CPF"
            error={errors.identifier?.message}
            description="Clientes entram com o usuário; a equipe, com o CPF."
          >
            <Input autoComplete="username" autoFocus {...form.register("identifier")} />
          </Field>
          <Field label="Senha" error={errors.password?.message}>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                className="pr-10"
                {...form.register("password")}
              />
              <Button
                variant="ghost"
                size="icon-sm"
                className="absolute top-0.5 right-0.5"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeOff /> : <Eye />}
              </Button>
            </div>
          </Field>
          <Button type="submit" size="lg" loading={login.isPending} className="mt-2">
            Entrar
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Ainda não tem conta?{" "}
          <Link to="/cadastro" className="font-medium text-primary hover:underline">
            Cadastre-se
          </Link>
          {" · "}
          <Link to="/" className="font-medium text-primary hover:underline">
            Ver cardápio
          </Link>
        </p>

        {SHOW_DEMO && (
          <div className="mt-8 rounded-lg border border-dashed bg-muted/40 p-4">
            <p className="flex items-center gap-2 text-sm font-medium">
              <Info className="size-4 text-info" aria-hidden /> Contas de demonstração
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Dados fictícios. Senha de todas: <code className="font-mono">{DEMO_PASSWORD}</code>
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {DEMO_ACCOUNTS.map((account) => (
                <Button
                  key={account.identifier}
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    form.setValue("identifier", account.identifier, { shouldValidate: true });
                    form.setValue("password", DEMO_PASSWORD, { shouldValidate: true });
                  }}
                >
                  {account.label}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>
    </AuthLayout>
  );
}
