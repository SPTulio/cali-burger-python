// Formatação para pt-BR. Horários são exibidos no fuso da lanchonete, o mesmo usado pelo
// backend para o relatório (TIMEZONE=America/Sao_Paulo).
export const STORE_TIMEZONE = "America/Sao_Paulo";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateTime = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: STORE_TIMEZONE,
});
const time = new Intl.DateTimeFormat("pt-BR", { timeStyle: "short", timeZone: STORE_TIMEZONE });
const dateOnly = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeZone: "UTC" });
const dayMonth = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", timeZone: "UTC" });
const longDate = new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeZone: "UTC" });

export function formatCurrency(value: string | number): string {
  return currency.format(typeof value === "string" ? Number(value) : value);
}

export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso));
}

export function formatTime(iso: string): string {
  return time.format(new Date(iso));
}

/** Datas sem hora ("2026-03-01") não podem passar pelo fuso, senão viram o dia anterior. */
export function formatDate(isoDate: string, style: "short" | "long" | "day-month" = "short"): string {
  const date = new Date(`${isoDate}T00:00:00Z`);
  if (style === "long") return longDate.format(date);
  if (style === "day-month") return dayMonth.format(date);
  return dateOnly.format(date);
}

export function formatRelative(iso: string, now: number = Date.now()): string {
  const minutes = Math.round((now - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return "agora";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `há ${hours} h`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "ontem" : `há ${days} dias`;
}

export function formatCpf(value: string): string {
  const d = value.replace(/\D/g, "").slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

/** Data de hoje no fuso da lanchonete, em YYYY-MM-DD. */
export function todayIso(offsetDays = 0): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: STORE_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(Date.now() + offsetDays * 86_400_000));
  return parts;
}

export function plural(count: number, singular: string, pluralForm: string): string {
  return `${count} ${count === 1 ? singular : pluralForm}`;
}

/** ISO + minutos → ISO (para janelas de previsão). */
export function addMinutes(iso: string, minutes: number): string {
  return new Date(new Date(iso).getTime() + minutes * 60_000).toISOString();
}
