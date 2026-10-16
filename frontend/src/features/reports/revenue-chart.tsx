import { useEffect, useRef, useState } from "react";

import { formatCurrency, formatDate } from "@/lib/format";

interface Point {
  date: string;
  revenue: number;
  orders: number;
}

const HEIGHT = 220;
const PADDING = { top: 12, right: 8, bottom: 28, left: 56 };
const MAX_BAR = 24;

function niceStep(max: number, ticks = 4): number {
  const raw = max / ticks;
  const magnitude = 10 ** Math.floor(Math.log10(raw || 1));
  const normalized = raw / magnitude;
  const nice = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return nice * magnitude;
}

function compactCurrency(value: number): string {
  if (value >= 1000) return `R$ ${(value / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mil`;
  return `R$ ${value.toLocaleString("pt-BR")}`;
}

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    if (!ref.current) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry!.contentRect.width));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

/** Faturamento por dia: uma série, colunas finas com ponta arredondada, dica ao passar o
 *  mouse ou focar pelo teclado. A tabela "Vendas por dia" traz os mesmos números. */
export function RevenueChart({ data }: { data: Point[] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [active, setActive] = useState<number | null>(null);

  const max = Math.max(...data.map((d) => d.revenue), 0);
  const step = niceStep(max);
  const top = Math.max(step, Math.ceil(max / step) * step);
  const ticks = Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step);

  const plotW = Math.max(0, width - PADDING.left - PADDING.right);
  const plotH = HEIGHT - PADDING.top - PADDING.bottom;
  const band = data.length ? plotW / data.length : 0;
  const barW = Math.max(2, Math.min(MAX_BAR, band - 2)); // 2px de respiro entre colunas
  const y = (v: number) => PADDING.top + plotH - (v / top) * plotH;
  const labelEvery = Math.max(1, Math.ceil(data.length / Math.max(1, Math.floor(plotW / 56))));

  const activePoint = active !== null ? data[active] : undefined;

  return (
    <div ref={ref} className="relative w-full" onMouseLeave={() => setActive(null)}>
      {width > 0 && (
        <svg width={width} height={HEIGHT} role="group" aria-label="Faturamento por dia">
          {ticks.map((t) => (
            <g key={t}>
              <line x1={PADDING.left} x2={width - PADDING.right} y1={y(t)} y2={y(t)} stroke="var(--border)" strokeWidth={1} />
              <text x={PADDING.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-muted-foreground text-[11px] tabular">
                {compactCurrency(t)}
              </text>
            </g>
          ))}
          {data.map((d, i) => {
            const cx = PADDING.left + band * i + band / 2;
            const x = cx - barW / 2;
            const barTop = y(d.revenue);
            const h = PADDING.top + plotH - barTop;
            const r = Math.min(4, barW / 2, h);
            return (
              <g
                key={d.date}
                tabIndex={0}
                role="img"
                aria-label={`${formatDate(d.date, "long")}: ${formatCurrency(d.revenue)} em ${d.orders} pedido(s)`}
                onMouseEnter={() => setActive(i)}
                onFocus={() => setActive(i)}
                onBlur={() => setActive(null)}
                className="outline-none"
              >
                {/* Área de toque maior que a coluna. */}
                <rect x={cx - band / 2} y={PADDING.top} width={band} height={plotH} fill="transparent" />
                {active === i && (
                  <rect x={cx - band / 2 + 1} y={PADDING.top} width={band - 2} height={plotH} rx={4} fill="var(--muted)" />
                )}
                {h > 0 && (
                  <path
                    d={`M${x},${barTop + h} V${barTop + r} Q${x},${barTop} ${x + r},${barTop} H${x + barW - r} Q${x + barW},${barTop} ${x + barW},${barTop + r} V${barTop + h} Z`}
                    fill="var(--chart-1)"
                  />
                )}
                {i % labelEvery === 0 && (
                  <text x={cx} y={HEIGHT - 8} textAnchor="middle" className="fill-muted-foreground text-[11px] tabular">
                    {formatDate(d.date, "day-month")}
                  </text>
                )}
              </g>
            );
          })}
          <line x1={PADDING.left} x2={width - PADDING.right} y1={y(0)} y2={y(0)} stroke="var(--input)" strokeWidth={1} />
        </svg>
      )}
      {activePoint && active !== null && (
        <div
          className="pointer-events-none absolute z-10 min-w-36 -translate-x-1/2 rounded-md border bg-surface px-3 py-2 text-xs shadow-lg"
          style={{
            left: Math.min(Math.max(PADDING.left + band * active + band / 2, 80), width - 80),
            top: Math.max(0, y(activePoint.revenue) - 64),
          }}
          role="status"
        >
          <p className="font-medium">{formatDate(activePoint.date, "long")}</p>
          <p className="tabular mt-0.5 text-sm font-semibold">{formatCurrency(activePoint.revenue)}</p>
          <p className="text-muted-foreground">{activePoint.orders} pedido(s)</p>
        </div>
      )}
    </div>
  );
}
