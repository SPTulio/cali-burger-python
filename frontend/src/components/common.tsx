import {
  ChevronLeft,
  ChevronRight,
  Minus,
  Moon,
  Plus,
  RefreshCw,
  Sun,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { errorMessage } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Badge, Skeleton } from "@/components/ui/primitives";
import { ORDER_STATUS, STOCK_LEVEL } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { Availability, OrderStatus, StockLevel } from "@/types/api";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center px-6 py-14 text-center", className)}>
      <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-muted">
        <Icon className="size-5 text-muted-foreground" aria-hidden />
      </div>
      <h3 className="text-base font-semibold">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <EmptyState
      icon={TriangleAlert}
      title="Não foi possível carregar"
      description={errorMessage(error)}
      action={
        onRetry && (
          <Button variant="outline" onClick={onRetry}>
            <RefreshCw /> Tentar novamente
          </Button>
        )
      }
    />
  );
}

export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="divide-y" aria-busy="true" aria-label="Carregando">
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} className="flex items-center gap-4 px-4 py-3.5">
          {Array.from({ length: columns }, (_, c) => (
            <Skeleton key={c} className={cn("h-4", c === 1 ? "flex-[2]" : "flex-1")} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function StatusBadge({ status }: { status: OrderStatus }) {
  const { label, tone } = ORDER_STATUS[status];
  return (
    <Badge tone={tone} dot>
      {label}
    </Badge>
  );
}

export function StockBadge({ level }: { level: StockLevel }) {
  const { label, tone } = STOCK_LEVEL[level];
  return <Badge tone={tone}>{label}</Badge>;
}

export function AvailabilityBadge({
  availability,
  portions,
}: {
  availability: Availability;
  portions: number | null;
}) {
  if (availability === "sold_out") return <Badge tone="danger">Esgotado</Badge>;
  if (availability === "low") return <Badge tone="warning">Últimas {portions}</Badge>;
  return <Badge tone="success">Disponível</Badge>;
}

export function Pagination({
  page,
  pages,
  total,
  pageSize,
  onPageChange,
}: {
  page: number;
  pages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}) {
  if (total === 0) return null;
  const first = (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);
  return (
    <nav
      className="flex items-center justify-between gap-3 border-t px-4 py-3 text-sm text-muted-foreground"
      aria-label="Paginação"
    >
      <span className="tabular">
        Mostrando {first}–{last} de {total}
      </span>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon-sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Página anterior"
        >
          <ChevronLeft />
        </Button>
        <span className="tabular px-2 text-foreground">
          {page} / {pages}
        </span>
        <Button
          variant="outline"
          size="icon-sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
          aria-label="Próxima página"
        >
          <ChevronRight />
        </Button>
      </div>
    </nav>
  );
}

export function QuantityStepper({
  value,
  onChange,
  min = 0,
  max,
  label,
  size = "md",
}: {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max: number;
  label: string;
  size?: "sm" | "md";
}) {
  const buttonSize = size === "sm" ? "icon-sm" : "icon";
  return (
    <div className="inline-flex items-center rounded-md border bg-surface" role="group" aria-label={label}>
      <Button
        variant="ghost"
        size={buttonSize}
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        aria-label={`Diminuir ${label}`}
      >
        <Minus />
      </Button>
      <span className="tabular min-w-8 text-center text-sm font-medium" aria-live="polite">
        {value}
      </span>
      <Button
        variant="ghost"
        size={buttonSize}
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        aria-label={`Aumentar ${label}`}
      >
        <Plus />
      </Button>
    </div>
  );
}

export function Logo({ compact = false, className }: { compact?: boolean; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <svg viewBox="0 0 32 32" className="size-8 shrink-0" aria-hidden>
        <rect width="32" height="32" rx="8" fill="var(--primary)" />
        <path d="M7 14.5C7 10 11 7 16 7s9 3 9 7.5H7Z" fill="#FFF7ED" />
        <rect x="6" y="16.5" width="20" height="3" rx="1.5" fill="#FDBA74" />
        <path d="M7 21.5h18c0 2-1.6 3.5-3.5 3.5h-11C8.6 25 7 23.5 7 21.5Z" fill="#FFF7ED" />
      </svg>
      {!compact && (
        <span className="text-[15px] leading-none font-semibold tracking-tight">
          Cali <span className="text-primary">Burger</span>
        </span>
      )}
    </span>
  );
}

function readTheme(): "light" | "dark" {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState(readTheme);
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("cb-theme", theme);
    } catch {
      // Navegação privada: o tema só não fica salvo.
    }
  }, [theme]);
  const next = theme === "dark" ? "light" : "dark";
  return (
    <Button
      variant="ghost"
      size="icon"
      className={className}
      onClick={() => setTheme(next)}
      aria-label={next === "dark" ? "Usar tema escuro" : "Usar tema claro"}
      title={next === "dark" ? "Tema escuro" : "Tema claro"}
    >
      {theme === "dark" ? <Sun /> : <Moon />}
    </Button>
  );
}

export function FullPageSpinner() {
  return (
    <div className="flex min-h-dvh items-center justify-center" aria-busy="true" aria-label="Carregando">
      <Logo compact className="animate-pulse" />
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon: LucideIcon;
}) {
  return (
    <div className="rounded-lg border bg-surface p-4 shadow-xs">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        {label}
        <Icon className="size-4" aria-hidden />
      </div>
      <div className="tabular mt-2 text-2xl font-semibold tracking-tight">{value}</div>
      {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}
