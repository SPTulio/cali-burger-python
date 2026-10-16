import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChefHat, Store, Trash, UserPlus, type LucideIcon } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

import { errorMessage } from "@/api/client";
import { staffApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { EmptyState, ErrorState, PageHeader, TableSkeleton } from "@/components/common";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog, DialogContent, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Field, Input, Select } from "@/components/ui/field";
import { Badge, Card, CardHeader, Table, TD, TH, THead, TR } from "@/components/ui/primitives";
import { useSession, useSetSession } from "@/features/auth/session";
import { formatCpf, formatDate, todayIso } from "@/lib/format";
import { SEX_LABEL } from "@/lib/labels";
import { applyApiErrors, fields, withCpfMask } from "@/lib/validation";
import type { StaffMember } from "@/types/api";

export function StaffPage() {
  const session = useSession();
  const setSession = useSetSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<StaffMember | null>(null);

  const staff = useQuery({ queryKey: queryKeys.staff, queryFn: staffApi.list });
  const remove = useMutation({
    mutationFn: (member: StaffMember) => staffApi.remove(member.id),
    onSuccess: (_, member) => {
      if (member.id === session.data?.id) {
        toast.success("Seu cadastro foi excluído.");
        setSession(null);
        navigate("/entrar", { replace: true });
        return;
      }
      toast.success(`${member.name} foi removido(a) da equipe.`);
      queryClient.invalidateQueries({ queryKey: queryKeys.staff });
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const managers = staff.data?.filter((s) => s.role === "manager") ?? [];
  const cooks = staff.data?.filter((s) => s.role === "cook") ?? [];

  const section = (title: string, description: string, members: StaffMember[], icon: LucideIcon) => (
    <Card>
      <CardHeader title={title} description={description} />
      {staff.isPending ? (
        <TableSkeleton rows={2} columns={4} />
      ) : members.length === 0 ? (
        <EmptyState icon={icon} title="Ninguém cadastrado" description="Use “Cadastrar funcionário” para adicionar." />
      ) : (
        <Table>
          <THead>
            <tr>
              <TH>Nome</TH>
              <TH>CPF</TH>
              <TH className="hidden md:table-cell">E-mail</TH>
              <TH className="hidden lg:table-cell">Nascimento</TH>
              <TH className="hidden lg:table-cell">Sexo</TH>
              <TH className="w-12">
                <span className="sr-only">Ações</span>
              </TH>
            </tr>
          </THead>
          <tbody>
            {members.map((member) => {
              const isMe = member.id === session.data?.id;
              return (
                <TR key={member.id}>
                  <TD className="font-medium">
                    {member.name} {isMe && <Badge tone="primary">Você</Badge>}
                  </TD>
                  <TD className="tabular whitespace-nowrap">{formatCpf(member.cpf)}</TD>
                  <TD className="hidden text-muted-foreground md:table-cell">{member.email}</TD>
                  <TD className="tabular hidden lg:table-cell">{formatDate(member.birth_date)}</TD>
                  <TD className="hidden lg:table-cell">{member.sex ? SEX_LABEL[member.sex] : "—"}</TD>
                  <TD>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setDeleting(member)}
                      aria-label={`Excluir ${member.name}`}
                    >
                      <Trash className="text-muted-foreground" />
                    </Button>
                  </TD>
                </TR>
              );
            })}
          </tbody>
        </Table>
      )}
    </Card>
  );

  return (
    <div>
      <PageHeader
        title="Equipe"
        description="Cadastre e gerencie quem trabalha na lanchonete. Funcionários entram com o CPF."
        actions={
          <Button onClick={() => setCreating(true)}>
            <UserPlus /> Cadastrar funcionário
          </Button>
        }
      />
      {staff.isError ? (
        <ErrorState error={staff.error} onRetry={() => staff.refetch()} />
      ) : (
        <div className="flex flex-col gap-6">
          {section("Balconistas e donos", "Gerenciam pedidos, cardápio, estoque, relatórios e equipe.", managers, Store)}
          {section("Cozinheiros", "Veem a fila de preparo e enviam os pedidos para entrega.", cooks, ChefHat)}
        </div>
      )}

      {creating && <CreateStaffDialog onClose={() => setCreating(false)} />}
      {deleting && (
        <ConfirmDialog
          open
          onOpenChange={(open) => !open && setDeleting(null)}
          title={deleting.id === session.data?.id ? "Excluir o seu cadastro?" : `Excluir ${deleting.name}?`}
          description={
            deleting.id === session.data?.id
              ? "Você será desconectado e não poderá mais entrar com este CPF. Esta ação não pode ser desfeita."
              : "A pessoa perde o acesso ao sistema imediatamente. Esta ação não pode ser desfeita."
          }
          confirmLabel="Excluir"
          destructive
          onConfirm={() => remove.mutateAsync(deleting)}
        />
      )}
    </div>
  );
}

const schema = z
  .object({
    role: z.enum(["manager", "cook"], { error: "Selecione a função." }),
    name: fields.required(100),
    cpf: fields.cpf,
    email: fields.email,
    birth_date: fields.birthDate,
    sex: z.enum(["male", "female", "other"], { error: "Selecione o sexo." }),
    password: fields.password,
    password_confirmation: z.string(),
  })
  .refine((d) => d.password === d.password_confirmation, {
    path: ["password_confirmation"],
    message: "As senhas não coincidem.",
  });
type StaffForm = z.input<typeof schema>;

function CreateStaffDialog({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const form = useForm<StaffForm, unknown, z.output<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      role: "cook",
      name: "",
      cpf: "",
      email: "",
      birth_date: "",
      sex: undefined,
      password: "",
      password_confirmation: "",
    },
  });
  const { errors } = form.formState;
  const create = useMutation({
    mutationFn: staffApi.create,
    onSuccess: (member) => {
      toast.success(`${member.name} cadastrado(a). Já pode entrar com o CPF e a senha definida.`);
      queryClient.invalidateQueries({ queryKey: queryKeys.staff });
      onClose();
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-xl">
        <DialogHeader title="Cadastrar funcionário" description="A senha pode ser trocada depois pelo próprio funcionário." />
        <form
          id="staff-form"
          className="grid gap-4 sm:grid-cols-2"
          onSubmit={form.handleSubmit((d) => create.mutate(d))}
          noValidate
        >
          <Field label="Função" error={errors.role?.message} className="sm:col-span-2">
            <Select {...form.register("role")}>
              <option value="cook">Cozinheiro</option>
              <option value="manager">Balconista / dono</option>
            </Select>
          </Field>
          <Field label="Nome completo" error={errors.name?.message} className="sm:col-span-2">
            <Input {...form.register("name")} />
          </Field>
          <Field label="CPF" error={errors.cpf?.message} description="Usado para entrar no sistema.">
            <Input inputMode="numeric" placeholder="000.000.000-00" {...withCpfMask(form.register("cpf"))} />
          </Field>
          <Field label="Data de nascimento" error={errors.birth_date?.message}>
            <Input type="date" max={todayIso()} {...form.register("birth_date")} />
          </Field>
          <Field label="E-mail" error={errors.email?.message}>
            <Input type="email" {...form.register("email")} />
          </Field>
          <Field label="Sexo" error={errors.sex?.message}>
            <Select defaultValue="" {...form.register("sex")}>
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
          <Field label="Senha inicial" error={errors.password?.message}>
            <Input type="password" autoComplete="new-password" {...form.register("password")} />
          </Field>
          <Field label="Confirmar senha" error={errors.password_confirmation?.message}>
            <Input type="password" autoComplete="new-password" {...form.register("password_confirmation")} />
          </Field>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form="staff-form" loading={create.isPending}>
            Cadastrar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
