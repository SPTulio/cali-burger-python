import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Identificador único para a chave de idempotência de uma tentativa de compra. */
export function newIdempotencyKey(): string {
  return crypto.randomUUID().replaceAll("-", "");
}
