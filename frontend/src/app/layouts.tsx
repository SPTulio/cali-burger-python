import { useQuery } from "@tanstack/react-query";
import {
  ChartColumn,
  ChefHat,
  ClipboardList,
  LogIn,
  LogOut,
  Menu as MenuIcon,
  Package,
  ReceiptText,
  ShoppingBag,
  Store,
  UserRound,
  Users,
  UtensilsCrossed,
  type LucideIcon,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";

import { ordersApi } from "@/api/endpoints";
import heroImage from "@/assets/hero.webp";
import { queryKeys } from "@/api/keys";
import { Logo, ThemeToggle } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Dialog, SheetContent } from "@/components/ui/dialog";
import { Menu, MenuContent, MenuItem, MenuLabel, MenuSeparator, MenuTrigger } from "@/components/ui/menu";
import { useLogout, useSession } from "@/features/auth/session";
import { CartSheet } from "@/features/cart/cart-sheet";
import { cartTotals, useCart } from "@/features/cart/store";
import { StoreBanner } from "@/features/store/store-banner";
import { ROLE_LABEL } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { User } from "@/types/api";

function SkipLink() {
  return (
    <a
      href="#conteudo"
      className="sr-only z-[60] rounded-md bg-primary px-3 py-2 text-primary-foreground focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
    >
      Pular para o conteúdo
    </a>
  );
}

function UserMenu({ user, links }: { user: User; links: { to: string; label: string; icon: LucideIcon }[] }) {
  const logout = useLogout();
  return (
    <Menu>
      <MenuTrigger asChild>
        <Button variant="ghost" className="gap-2 px-2" aria-label={`Menu de ${user.first_name}`}>
          <span className="flex size-7 items-center justify-center rounded-full bg-primary-soft text-[13px] font-semibold text-primary">
            {user.first_name.charAt(0).toUpperCase()}
          </span>
          <span className="hidden max-w-28 truncate sm:inline">{user.first_name}</span>
        </Button>
      </MenuTrigger>
      <MenuContent>
        <MenuLabel>
          <span className="block truncate font-medium text-foreground">{user.name}</span>
          {ROLE_LABEL[user.role]}
        </MenuLabel>
        <MenuSeparator />
        {links.map(({ to, label, icon: Icon }) => (
          <MenuItem key={to} asChild>
            <Link to={to}>
              <Icon /> {label}
            </Link>
          </MenuItem>
        ))}
        <MenuSeparator />
        <MenuItem onSelect={() => logout.mutate()} disabled={logout.isPending}>
          <LogOut /> Sair
        </MenuItem>
      </MenuContent>
    </Menu>
  );
}

// ------------------------------------------------------------------ vitrine do cliente

export function StorefrontLayout() {
  const session = useSession();
  const user = session.data;
  const lines = useCart((s) => s.lines);
  const { count } = cartTotals(lines);
  const [cartOpen, setCartOpen] = useState(false);

  const navLink = ({ isActive }: { isActive: boolean }) =>
    cn(
      "rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-muted",
      isActive ? "text-foreground" : "text-muted-foreground",
    );

  return (
    <div className="flex min-h-dvh flex-col">
      <SkipLink />
      <header className="sticky top-0 z-40 border-b bg-surface/90 backdrop-blur supports-[backdrop-filter]:bg-surface/75">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-2 px-4 sm:px-6">
          <Link to="/" className="mr-2 rounded-md" aria-label="Cali Burger — página inicial">
            <Logo />
          </Link>
          <nav className="hidden items-center gap-1 sm:flex" aria-label="Principal">
            <NavLink to="/" end className={navLink}>
              Cardápio
            </NavLink>
            {user?.role === "customer" && (
              <NavLink to="/pedidos" className={navLink}>
                Meus pedidos
              </NavLink>
            )}
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <Button
              variant="outline"
              className="relative"
              onClick={() => setCartOpen(true)}
              aria-label={`Abrir carrinho, ${count} ${count === 1 ? "item" : "itens"}`}
            >
              <ShoppingBag />
              <span className="hidden sm:inline">Carrinho</span>
              {count > 0 && (
                <span className="tabular absolute -top-1.5 -right-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[11px] font-semibold text-primary-foreground">
                  {count}
                </span>
              )}
            </Button>
            {user ? (
              <UserMenu
                user={user}
                links={[
                  { to: "/pedidos", label: "Meus pedidos", icon: ReceiptText },
                  { to: "/perfil", label: "Meu perfil", icon: UserRound },
                ]}
              />
            ) : (
              !session.isPending && (
                <Button asChild variant="ghost">
                  <Link to="/entrar">
                    <LogIn /> Entrar
                  </Link>
                </Button>
              )
            )}
          </div>
        </div>
      </header>
      <StoreBanner />
      <main id="conteudo" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
        <Outlet context={{ openCart: () => setCartOpen(true) }} />
      </main>
      <footer className="border-t py-6 text-center text-xs text-muted-foreground">
        Cali Burger · projeto de portfólio · pagamentos PIX simulados, nenhum valor é cobrado ·{" "}
        <Link to="/privacidade" className="underline-offset-4 hover:text-foreground hover:underline">
          Política de Privacidade
        </Link>
      </footer>
      <CartSheet open={cartOpen} onOpenChange={setCartOpen} />
    </div>
  );
}

export interface StorefrontContext {
  openCart: () => void;
}

// ------------------------------------------------------------------ painel da equipe

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  badge?: number;
}

function SidebarNav({ items, onNavigate }: { items: NavItem[]; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-0.5" aria-label="Seções">
      {items.map(({ to, label, icon: Icon, badge }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/cozinha"}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "relative flex h-9 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors",
              isActive
                ? "bg-muted text-foreground before:absolute before:top-2 before:bottom-2 before:-left-3 before:w-0.5 before:rounded-full before:bg-primary"
                : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
            )
          }
        >
          <Icon className="size-4" aria-hidden />
          {label}
          {badge ? (
            <span
              className="tabular ml-auto rounded-full bg-primary px-1.5 py-px text-[11px] font-semibold text-primary-foreground"
              aria-label={`${badge} pendentes`}
            >
              {badge}
            </span>
          ) : null}
        </NavLink>
      ))}
    </nav>
  );
}

export function StaffLayout({ area }: { area: "manager" | "cook" }) {
  const session = useSession();
  const user = session.data!;
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Contador de pendentes atualizado sozinho (sem recarregar a página).
  const summary = useQuery({
    queryKey: queryKeys.ordersSummary,
    queryFn: ordersApi.summary,
    refetchInterval: 20_000,
  });
  const counts = summary.data?.counts ?? {};

  const items: NavItem[] =
    area === "manager"
      ? [
          { to: "/painel/pedidos", label: "Pedidos", icon: ClipboardList, badge: counts.awaiting_acceptance },
          { to: "/painel/cardapio", label: "Cardápio", icon: UtensilsCrossed },
          { to: "/painel/estoque", label: "Estoque", icon: Package },
          { to: "/painel/relatorios", label: "Relatório de vendas", icon: ChartColumn },
          { to: "/painel/equipe", label: "Equipe", icon: Users },
          { to: "/painel/loja", label: "Loja e horários", icon: Store },
        ]
      : [
          { to: "/cozinha", label: "Fila da cozinha", icon: ChefHat, badge: counts.in_preparation },
          { to: "/cozinha/cardapio", label: "Cardápio e receitas", icon: UtensilsCrossed },
        ];
  const profilePath = area === "manager" ? "/painel/perfil" : "/cozinha/perfil";

  const sidebar = (onNavigate?: () => void): ReactNode => (
    <div className="flex h-full flex-col gap-6 p-4">
      <Link to={items[0]!.to} className="rounded-md px-2 pt-1" onClick={onNavigate}>
        <Logo />
      </Link>
      <div className="px-3">
        <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {area === "manager" ? "Gestão" : "Cozinha"}
        </p>
        <div className="-mx-3">
          <SidebarNav items={items} onNavigate={onNavigate} />
        </div>
      </div>
      <div className="mt-auto flex items-center justify-between gap-2 border-t pt-4">
        <UserMenu user={user} links={[{ to: profilePath, label: "Meu perfil", icon: UserRound }]} />
        <ThemeToggle />
      </div>
    </div>
  );

  return (
    <div className="min-h-dvh lg:pl-60">
      <SkipLink />
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r bg-surface lg:block">{sidebar()}</aside>
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-surface px-4 lg:hidden">
        <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)} aria-label="Abrir menu">
          <MenuIcon />
        </Button>
        <Logo />
      </header>
      <Dialog open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" title="Menu">
          {sidebar(() => setMobileOpen(false))}
        </SheetContent>
      </Dialog>
      <main id="conteudo" key={location.pathname} className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Outlet />
      </main>
    </div>
  );
}

// ------------------------------------------------------------------ autenticação

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1fr_1.1fr]">
      <div className="relative hidden overflow-hidden bg-stone-950 lg:block">
        <img src={heroImage} alt="" className="absolute inset-0 size-full object-cover opacity-55" />
        <div className="absolute inset-0 bg-gradient-to-t from-stone-950 via-stone-950/40 to-transparent" />
        <div className="relative flex h-full flex-col justify-between p-10 text-white">
          <Logo className="[&_span]:text-white" />
          <div className="max-w-md">
            <p className="text-3xl leading-tight font-semibold tracking-tight">
              Lanches artesanais, do pedido à entrega, com acompanhamento em tempo real.
            </p>
            <p className="mt-3 text-sm text-white/70">
              Clientes pedem pelo cardápio; a equipe aceita, prepara e entrega — com o estoque
              atualizado a cada pedido.
            </p>
          </div>
        </div>
      </div>
      <div className="flex flex-col">
        <div className="flex items-center justify-between p-4 sm:p-6">
          <Link to="/" className="rounded-md lg:invisible">
            <Logo />
          </Link>
          <ThemeToggle />
        </div>
        <main id="conteudo" className="flex flex-1 items-center justify-center px-4 pb-10 sm:px-6">
          {children}
        </main>
        <footer className="pb-6 text-center text-xs text-muted-foreground">
          <Link to="/privacidade" className="underline-offset-4 hover:text-foreground hover:underline">
            Política de Privacidade
          </Link>
        </footer>
      </div>
    </div>
  );
}
