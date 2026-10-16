// Validações de formulário espelhando as do backend (feedback imediato, sem ida ao servidor).
import type { FieldValues, Path, UseFormRegisterReturn, UseFormSetError } from "react-hook-form";
import { z } from "zod";

import { ApiError } from "@/api/client";
import { formatCpf } from "@/lib/format";

export function isValidCpf(value: string): boolean {
  const cpf = value.replace(/\D/g, "");
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
  for (const size of [9, 10]) {
    let total = 0;
    for (let i = 0; i < size; i++) total += Number(cpf[i]) * (size + 1 - i);
    if (Number(cpf[size]) !== ((total * 10) % 11) % 10) return false;
  }
  return true;
}

const REQUIRED = "Campo obrigatório.";

export const fields = {
  required: (max: number) =>
    z.string().trim().min(1, REQUIRED).max(max, `Use no máximo ${max} caracteres.`),
  optional: (max: number) => z.string().trim().max(max, `Use no máximo ${max} caracteres.`),
  cpf: z
    .string()
    .trim()
    .min(1, REQUIRED)
    .refine(isValidCpf, "CPF inválido."),
  username: z
    .string()
    .trim()
    .regex(
      /^[A-Za-z0-9._-]{3,30}$/,
      "Use de 3 a 30 caracteres: letras, números, ponto, hífen ou sublinhado.",
    ),
  email: z.string().trim().min(1, REQUIRED).max(255).pipe(z.email("E-mail inválido.")),
  password: z
    .string()
    .min(6, "A senha deve ter de 6 a 72 caracteres.")
    .max(72, "A senha deve ter de 6 a 72 caracteres."),
  birthDate: z
    .string()
    .min(1, REQUIRED)
    .refine((v) => {
      const date = new Date(`${v}T00:00:00Z`);
      return !Number.isNaN(date.getTime()) && v >= "1900-01-01" && date.getTime() <= Date.now();
    }, "Informe uma data de nascimento válida."),
};

export const addressSchema = z.object({
  street: fields.required(255),
  district: fields.required(255),
  city: fields.required(255),
  state: fields.required(255),
});

/** Leva os erros por campo da API para o formulário. Retorna true se aplicou algum. */
export function applyApiErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fieldMap: Record<string, Path<T>> = {},
): boolean {
  if (!(error instanceof ApiError)) return false;
  const entries = Object.entries(error.fields);
  for (const [field, message] of entries) {
    const target = (fieldMap[field] ?? field) as Path<T>;
    setError(target, { type: "server", message }, { shouldFocus: true });
  }
  return entries.length > 0;
}

/** Aplica a máscara 000.000.000-00 enquanto o usuário digita. */
export function withCpfMask<T extends string>(field: UseFormRegisterReturn<T>): UseFormRegisterReturn<T> {
  return {
    ...field,
    onChange: (event) => {
      const target = event.target as HTMLInputElement;
      target.value = formatCpf(target.value);
      return field.onChange(event);
    },
  };
}
