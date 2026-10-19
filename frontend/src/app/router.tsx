import type { ComponentType } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router";

import { RedirectIfAuthenticated, RequireRole } from "@/app/guards";
import { StaffLayout, StorefrontLayout } from "@/app/layouts";
import { NotFound, RouteError } from "@/app/route-pages";
import { LoginPage } from "@/features/auth/login-page";
import { RegisterPage } from "@/features/auth/register-page";
import { CheckoutPage } from "@/features/checkout/checkout-page";
import { PrivacyPage } from "@/features/legal/privacy-page";
import { MenuPage } from "@/features/menu/menu-page";
import { MyOrdersPage } from "@/features/orders/my-orders-page";
import { OrderDetailPage } from "@/features/orders/order-detail-page";
import { ProfilePage } from "@/features/profile/profile-page";

// As telas da equipe são carregadas sob demanda: o cliente não baixa o código do painel.
function page<K extends string>(load: () => Promise<Record<K, ComponentType>>, name: K) {
  return async () => ({ Component: (await load())[name] });
}

export const router = createBrowserRouter([
  {
    errorElement: <RouteError />,
    children: [
      {
        path: "/entrar",
        element: (
          <RedirectIfAuthenticated>
            <LoginPage />
          </RedirectIfAuthenticated>
        ),
      },
      {
        path: "/cadastro",
        element: (
          <RedirectIfAuthenticated>
            <RegisterPage />
          </RedirectIfAuthenticated>
        ),
      },
      {
        // Vitrine: o cardápio é público (como no original); o resto exige login de cliente.
        element: <StorefrontLayout />,
        children: [
          { index: true, element: <MenuPage /> },
          { path: "privacidade", element: <PrivacyPage /> },
          {
            element: (
              <RequireRole roles={["customer"]}>
                <Outlet />
              </RequireRole>
            ),
            children: [
              { path: "checkout", element: <CheckoutPage /> },
              { path: "pedidos", element: <MyOrdersPage /> },
              { path: "pedidos/:id", element: <OrderDetailPage /> },
              { path: "perfil", element: <ProfilePage /> },
            ],
          },
          { path: "*", element: <NotFound /> },
        ],
      },
      {
        path: "/painel",
        element: (
          <RequireRole roles={["manager"]}>
            <StaffLayout area="manager" />
          </RequireRole>
        ),
        children: [
          { index: true, element: <Navigate to="pedidos" replace /> },
          { path: "pedidos", lazy: page(() => import("@/features/orders/manage-orders-page"), "ManageOrdersPage") },
          { path: "pedidos/:id", element: <OrderDetailPage backTo="/painel/pedidos?visao=todos" /> },
          { path: "cardapio", lazy: page(() => import("@/features/catalog/menu-admin-page"), "MenuAdminPage") },
          { path: "cardapio/novo", lazy: page(() => import("@/features/catalog/menu-item-form-page"), "MenuItemFormPage") },
          { path: "cardapio/:id", lazy: page(() => import("@/features/catalog/menu-item-form-page"), "MenuItemFormPage") },
          { path: "estoque", lazy: page(() => import("@/features/inventory/inventory-page"), "InventoryPage") },
          { path: "relatorios", lazy: page(() => import("@/features/reports/reports-page"), "ReportsPage") },
          { path: "equipe", lazy: page(() => import("@/features/staff/staff-page"), "StaffPage") },
          { path: "loja", lazy: page(() => import("@/features/store/store-page"), "StorePage") },
          { path: "perfil", element: <ProfilePage /> },
          { path: "*", element: <NotFound /> },
        ],
      },
      {
        path: "/cozinha",
        element: (
          <RequireRole roles={["cook"]}>
            <StaffLayout area="cook" />
          </RequireRole>
        ),
        children: [
          { index: true, lazy: page(() => import("@/features/kitchen/kitchen-page"), "KitchenPage") },
          {
            path: "cardapio",
            lazy: async () => {
              const { MenuAdminPage } = await import("@/features/catalog/menu-admin-page");
              return { Component: () => <MenuAdminPage readOnly /> };
            },
          },
          { path: "perfil", element: <ProfilePage /> },
          { path: "*", element: <NotFound /> },
        ],
      },
    ],
  },
]);
