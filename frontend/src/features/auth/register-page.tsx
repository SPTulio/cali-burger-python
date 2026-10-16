import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

import { errorMessage } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { AuthLayout } from "@/app/layouts";
import { Button } from "@/components/ui/button";
import { Field, FormError, Input } from "@/components/ui/field";
import { useSetSession } from "@/features/auth/session";
import { todayIso } from "@/lib/format";
import { addressSchema, applyApiErrors, fields, withCpfMask } from "@/lib/validation";

const schema = z
  .object({
    username: fields.username,
    password: fields.password,
    password_confirmation: z.string(),
    name: fields.required(100),
    email: fields.email,
    cpf: fields.cpf,
    birth_date: fields.birthDate,
    address: addressSchema,
  })
  .refine((d) => d.password === d.password_confirmation, {
    path: ["password_confirmation"],
    message: "As senhas não coincidem.",
  });
type RegisterForm = z.infer<typeof schema>;

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="grid gap-4 sm:grid-cols-2">
      <legend className="mb-3 text-sm font-semibold">{title}</legend>
      {children}
    </fieldset>
  );
}

export function RegisterPage() {
  const setSession = useSetSession();
  const form = useForm<RegisterForm>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: "",
      password: "",
      password_confirmation: "",
      name: "",
      email: "",
      cpf: "",
      birth_date: "",
      address: { street: "", district: "", city: "", state: "" },
    },
  });
  const { errors } = form.formState;

  const signUp = useMutation({
    mutationFn: authApi.register,
    onSuccess: ({ user }) => {
      setSession(user);
      toast.success(`Bem-vindo(a), ${user.first_name}! Sua conta foi criada.`);
    },
    onError: (error) => applyApiErrors(error, form.setError),
  });

  return (
    <AuthLayout>
      <div className="w-full max-w-xl py-4">
        <h1 className="text-2xl font-semibold tracking-tight">Criar conta</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Leva um minuto. Você já entra na conta ao terminar.
        </p>

        <form
          className="mt-8 flex flex-col gap-8"
          onSubmit={form.handleSubmit((data) => signUp.mutate(data))}
          noValidate
        >
          {signUp.isError && !Object.keys(errors).length && (
            <FormError message={errorMessage(signUp.error)} />
          )}

          <Section title="Acesso">
            <Field label="Usuário" error={errors.username?.message} className="sm:col-span-2"
              description="De 3 a 30 caracteres: letras, números, ponto, hífen ou sublinhado.">
              <Input autoComplete="username" {...form.register("username")} />
            </Field>
            <Field label="Senha" error={errors.password?.message} description="Mínimo de 6 caracteres.">
              <Input type="password" autoComplete="new-password" {...form.register("password")} />
            </Field>
            <Field label="Confirmar senha" error={errors.password_confirmation?.message}>
              <Input
                type="password"
                autoComplete="new-password"
                {...form.register("password_confirmation")}
              />
            </Field>
          </Section>

          <Section title="Dados pessoais">
            <Field label="Nome completo" error={errors.name?.message} className="sm:col-span-2">
              <Input autoComplete="name" {...form.register("name")} />
            </Field>
            <Field label="E-mail" error={errors.email?.message} className="sm:col-span-2">
              <Input type="email" autoComplete="email" {...form.register("email")} />
            </Field>
            <Field label="CPF" error={errors.cpf?.message}>
              <Input
                inputMode="numeric"
                placeholder="000.000.000-00"
                {...withCpfMask(form.register("cpf"))}
              />
            </Field>
            <Field label="Data de nascimento" error={errors.birth_date?.message}>
              <Input type="date" max={todayIso()} min="1900-01-01" {...form.register("birth_date")} />
            </Field>
          </Section>

          <Section title="Endereço de entrega">
            <Field label="Logradouro" error={errors.address?.street?.message} className="sm:col-span-2">
              <Input
                autoComplete="street-address"
                placeholder="Rua, número e complemento"
                {...form.register("address.street")}
              />
            </Field>
            <Field label="Bairro" error={errors.address?.district?.message}>
              <Input {...form.register("address.district")} />
            </Field>
            <Field label="Cidade" error={errors.address?.city?.message}>
              <Input autoComplete="address-level2" {...form.register("address.city")} />
            </Field>
            <Field label="Estado" error={errors.address?.state?.message}>
              <Input autoComplete="address-level1" placeholder="PR" {...form.register("address.state")} />
            </Field>
          </Section>

          <div className="flex flex-col gap-3">
            <Button type="submit" size="lg" loading={signUp.isPending}>
              Criar conta
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Já tem conta?{" "}
              <Link to="/entrar" className="font-medium text-primary hover:underline">
                Entrar
              </Link>
            </p>
          </div>
        </form>
      </div>
    </AuthLayout>
  );
}
