import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

import { errorMessage } from "@/api/client";
import { accountApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { ErrorState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Field, Input, Select } from "@/components/ui/field";
import { Card, CardHeader, Skeleton } from "@/components/ui/primitives";
import { useSetSession } from "@/features/auth/session";
import { useCart } from "@/features/cart/store";
import { formatCpf, todayIso } from "@/lib/format";
import { ROLE_LABEL, SEX_LABEL } from "@/lib/labels";
import { addressSchema, applyApiErrors, fields, withCpfMask } from "@/lib/validation";
import type { Address, Profile, Sex } from "@/types/api";

export function ProfilePage() {
  const profile = useQuery({ queryKey: queryKeys.profile, queryFn: accountApi.profile });

  if (profile.isPending) return <Skeleton className="mx-auto h-[520px] max-w-3xl" />;
  if (profile.isError) return <ErrorState error={profile.error} onRetry={() => profile.refetch()} />;
  const data = profile.data;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <PageHeader title="Meu perfil" description={`${ROLE_LABEL[data.role]} · ${data.name}`} />
      <PersonalDataCard profile={data} />
      {data.role === "customer" && <AddressCard address={data.address} />}
      <PasswordCard />
      {data.role !== "cook" && <DeleteAccountCard profile={data} />}
    </div>
  );
}

// Clientes editam usuário e CPF; funcionários editam o sexo (o CPF deles é fixo).
const personalSchema = (isCustomer: boolean) =>
  z.object({
    username: isCustomer ? fields.username : z.string(),
    name: fields.required(100),
    email: fields.email,
    cpf: isCustomer ? fields.cpf : z.string(),
    birth_date: fields.birthDate,
    sex: isCustomer ? z.string() : z.enum(["male", "female", "other"], { error: "Selecione o sexo." }),
  });
type PersonalForm = { username: string; name: string; email: string; cpf: string; birth_date: string; sex: string };

function PersonalDataCard({ profile }: { profile: Profile }) {
  const isCustomer = profile.role === "customer";
  const queryClient = useQueryClient();
  const form = useForm<PersonalForm>({
    resolver: zodResolver(personalSchema(isCustomer)),
    defaultValues: {
      username: profile.username ?? "",
      name: profile.name,
      email: profile.email,
      cpf: formatCpf(profile.cpf),
      birth_date: profile.birth_date,
      sex: profile.sex ?? "",
    },
  });
  const { errors, isDirty } = form.formState;
  const save = useMutation({
    mutationFn: (data: PersonalForm) =>
      accountApi.updateProfile(
        isCustomer
          ? { name: data.name, email: data.email, birth_date: data.birth_date, username: data.username, cpf: data.cpf }
          : { name: data.name, email: data.email, birth_date: data.birth_date, sex: data.sex as Sex },
      ),
    onSuccess: (updated) => {
      toast.success("Dados atualizados.");
      queryClient.setQueryData(queryKeys.profile, updated);
      queryClient.invalidateQueries({ queryKey: queryKeys.session });
      form.reset({ ...form.getValues() });
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });

  return (
    <Card>
      <CardHeader title="Dados pessoais" />
      <form className="grid gap-4 p-5 sm:grid-cols-2" onSubmit={form.handleSubmit((d) => save.mutate(d))} noValidate>
        {isCustomer && (
          <Field label="Usuário" error={errors.username?.message} description="Usado para entrar no sistema.">
            <Input autoComplete="username" {...form.register("username")} />
          </Field>
        )}
        <Field label="Nome completo" error={errors.name?.message} className={isCustomer ? undefined : "sm:col-span-2"}>
          <Input autoComplete="name" {...form.register("name")} />
        </Field>
        <Field label="E-mail" error={errors.email?.message}>
          <Input type="email" autoComplete="email" {...form.register("email")} />
        </Field>
        {isCustomer ? (
          <Field label="CPF" error={errors.cpf?.message}>
            <Input inputMode="numeric" {...withCpfMask(form.register("cpf"))} />
          </Field>
        ) : (
          <Field label="CPF" description="Usado para entrar; não pode ser alterado.">
            <Input value={formatCpf(profile.cpf)} readOnly disabled />
          </Field>
        )}
        <Field label="Data de nascimento" error={errors.birth_date?.message}>
          <Input type="date" max={todayIso()} {...form.register("birth_date")} />
        </Field>
        {!isCustomer && (
          <Field label="Sexo" error={errors.sex?.message}>
            <Select {...form.register("sex")}>
              <option value="" disabled>
                Selecione
              </option>
              {Object.entries(SEX_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </Field>
        )}
        <div className="flex justify-end sm:col-span-2">
          <Button type="submit" loading={save.isPending} disabled={!isDirty}>
            Salvar dados
          </Button>
        </div>
      </form>
    </Card>
  );
}

function AddressCard({ address }: { address: Address | null }) {
  const queryClient = useQueryClient();
  const form = useForm<Address>({
    resolver: zodResolver(addressSchema),
    defaultValues: address ?? { street: "", district: "", city: "", state: "" },
  });
  const { errors, isDirty } = form.formState;
  const save = useMutation({
    mutationFn: accountApi.updateAddress,
    onSuccess: (updated) => {
      toast.success("Endereço atualizado.");
      queryClient.invalidateQueries({ queryKey: queryKeys.profile });
      form.reset(updated);
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });
  return (
    <Card>
      <CardHeader title="Endereço de entrega" description="Usado nos próximos pedidos." />
      <form className="grid gap-4 p-5 sm:grid-cols-2" onSubmit={form.handleSubmit((d) => save.mutate(d))} noValidate>
        <Field label="Logradouro" error={errors.street?.message} className="sm:col-span-2">
          <Input placeholder="Rua, número e complemento" autoComplete="street-address" {...form.register("street")} />
        </Field>
        <Field label="Bairro" error={errors.district?.message}>
          <Input {...form.register("district")} />
        </Field>
        <Field label="Cidade" error={errors.city?.message}>
          <Input autoComplete="address-level2" {...form.register("city")} />
        </Field>
        <Field label="Estado" error={errors.state?.message}>
          <Input autoComplete="address-level1" {...form.register("state")} />
        </Field>
        <div className="flex items-end justify-end">
          <Button type="submit" loading={save.isPending} disabled={!isDirty}>
            Salvar endereço
          </Button>
        </div>
      </form>
    </Card>
  );
}

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Informe a senha atual."),
    new_password: fields.password,
    new_password_confirmation: z.string(),
  })
  .refine((d) => d.new_password === d.new_password_confirmation, {
    path: ["new_password_confirmation"],
    message: "As senhas não coincidem.",
  });
type PasswordForm = z.infer<typeof passwordSchema>;

function PasswordCard() {
  const form = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: "", new_password: "", new_password_confirmation: "" },
  });
  const { errors } = form.formState;
  const save = useMutation({
    mutationFn: accountApi.changePassword,
    onSuccess: () => {
      toast.success("Senha alterada. Outras sessões abertas foram encerradas.");
      form.reset();
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });
  return (
    <Card>
      <CardHeader title="Senha" description="Ao trocar, você continua conectado aqui e é desconectado dos outros dispositivos." />
      <form className="grid gap-4 p-5 sm:grid-cols-3" onSubmit={form.handleSubmit((d) => save.mutate(d))} noValidate>
        <Field label="Senha atual" error={errors.current_password?.message}>
          <Input type="password" autoComplete="current-password" {...form.register("current_password")} />
        </Field>
        <Field label="Nova senha" error={errors.new_password?.message}>
          <Input type="password" autoComplete="new-password" {...form.register("new_password")} />
        </Field>
        <Field label="Confirmar nova senha" error={errors.new_password_confirmation?.message}>
          <Input type="password" autoComplete="new-password" {...form.register("new_password_confirmation")} />
        </Field>
        <div className="flex justify-end sm:col-span-3">
          <Button type="submit" variant="outline" loading={save.isPending}>
            Trocar senha
          </Button>
        </div>
      </form>
    </Card>
  );
}

function DeleteAccountCard({ profile }: { profile: Profile }) {
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const setSession = useSetSession();
  const clearCart = useCart((s) => s.clear);
  const navigate = useNavigate();

  async function confirm() {
    setError(null);
    try {
      await accountApi.deleteAccount(password);
    } catch (err) {
      setError(errorMessage(err));
      throw err;
    }
    clearCart();
    setSession(null);
    toast.success("Sua conta foi excluída.");
    navigate("/entrar", { replace: true });
  }

  return (
    <Card className="border-destructive/30">
      <CardHeader
        title="Excluir conta"
        description={
          profile.role === "customer"
            ? "Seus dados pessoais são apagados. Os pedidos já feitos continuam no histórico da lanchonete, apenas com o seu nome."
            : "Você perde o acesso ao painel. Não é possível excluir o último balconista."
        }
        actions={
          <Button variant="destructive-outline" onClick={() => setOpen(true)}>
            Excluir minha conta
          </Button>
        }
      />
      <ConfirmDialog
        open={open}
        onOpenChange={(next) => {
          setOpen(next);
          if (!next) {
            setPassword("");
            setError(null);
          }
        }}
        title="Excluir sua conta?"
        description="Esta ação não pode ser desfeita. Digite sua senha para confirmar."
        confirmLabel="Excluir conta"
        destructive
        onConfirm={confirm}
      >
        <Field label="Senha" error={error ?? undefined}>
          <Input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </Field>
      </ConfirmDialog>
    </Card>
  );
}
