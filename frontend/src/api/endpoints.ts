// Todas as chamadas à API em um só lugar, agrupadas por domínio.
import { http } from "@/api/client";
import type {
  Address,
  Category,
  IngredientAddResult,
  Ingredient,
  Inventory,
  MenuItem,
  MenuItemInput,
  Order,
  OrderAction,
  OrderActionResult,
  OrderFilters,
  OrderStatus,
  Page,
  Profile,
  Role,
  SalesReport,
  SessionResponse,
  Sex,
  StaffMember,
  StoreStatus,
} from "@/types/api";

export interface RegisterInput {
  username: string;
  password: string;
  password_confirmation: string;
  name: string;
  email: string;
  cpf: string;
  birth_date: string;
  address: Address;
}

export interface ProfileInput {
  name: string;
  email: string;
  birth_date: string;
  username?: string;
  cpf?: string;
  sex?: Sex;
}

export interface StaffInput {
  role: Exclude<Role, "customer">;
  cpf: string;
  name: string;
  birth_date: string;
  email: string;
  sex: Sex;
  password: string;
  password_confirmation: string;
}

export const authApi = {
  me: () => http.get<SessionResponse>("/auth/me"),
  login: (identifier: string, password: string) =>
    http.post<SessionResponse>("/auth/login", { json: { identifier, password } }),
  register: (data: RegisterInput) => http.post<SessionResponse>("/auth/register", { json: data }),
  logout: () => http.post<void>("/auth/logout"),
};

export const accountApi = {
  profile: () => http.get<Profile>("/me/profile"),
  updateProfile: (data: ProfileInput) => http.put<Profile>("/me/profile", { json: data }),
  updateAddress: (data: Address) => http.put<Address>("/me/address", { json: data }),
  changePassword: (data: {
    current_password: string;
    new_password: string;
    new_password_confirmation: string;
  }) => http.post<void>("/me/password", { json: data }),
  deleteAccount: (password: string) => http.delete<void>("/me", { json: { password } }),
};

export const catalogApi = {
  categories: () => http.get<Category[]>("/categories"),
  menu: (categoryId?: number) =>
    http.get<MenuItem[]>("/menu-items", { params: { category_id: categoryId } }),
  item: (id: number) => http.get<MenuItem>(`/menu-items/${id}`),
  create: (data: MenuItemInput) => http.post<MenuItem>("/menu-items", { json: data }),
  update: (id: number, data: MenuItemInput) =>
    http.put<MenuItem>(`/menu-items/${id}`, { json: data }),
  remove: (id: number) => http.delete<void>(`/menu-items/${id}`),
  uploadImage: (id: number, file: File) => {
    const body = new FormData();
    body.append("image", file);
    return http.put<MenuItem>(`/menu-items/${id}/image`, { body });
  },
  removeImage: (id: number) => http.delete<MenuItem>(`/menu-items/${id}/image`),
  setPaused: (id: number, paused: boolean) =>
    http.put<MenuItem>(`/menu-items/${id}/pause`, { json: { paused } }),
};

export const inventoryApi = {
  list: (q?: string) => http.get<Inventory>("/ingredients", { params: { q } }),
  add: (name: string, quantity: number) =>
    http.post<IngredientAddResult>("/ingredients", { json: { name, quantity } }),
  update: (id: number, name: string, quantity: number) =>
    http.put<Ingredient>(`/ingredients/${id}`, { json: { name, quantity } }),
  remove: (id: number) => http.delete<void>(`/ingredients/${id}`),
};

export const ordersApi = {
  list: (filters: OrderFilters) =>
    http.get<Page<Order>>("/orders", { params: { ...filters } }),
  get: (id: number) => http.get<Order>(`/orders/${id}`),
  summary: () => http.get<{ counts: Partial<Record<OrderStatus, number>> }>("/orders/summary"),
  create: (items: { menu_item_id: number; quantity: number; notes: string | null }[], key: string) =>
    http.post<Order>("/orders", { json: { items }, headers: { "Idempotency-Key": key } }),
  act: (id: number, action: OrderAction) =>
    http.post<OrderActionResult>(`/orders/${id}/actions/${action}`),
};

export const reportsApi = {
  sales: (start?: string, end?: string) =>
    http.get<SalesReport>("/reports/sales", { params: { start, end } }),
};

export const staffApi = {
  list: () => http.get<StaffMember[]>("/staff"),
  create: (data: StaffInput) => http.post<StaffMember>("/staff", { json: data }),
  remove: (id: number) => http.delete<void>(`/staff/${id}`),
};

export const storeApi = {
  status: () => http.get<StoreStatus>("/store"),
  replaceHours: (hours: { weekday: number; opens_at: string; closes_at: string }[]) =>
    http.put<StoreStatus>("/store/hours", { json: { hours } }),
  setPause: (paused: boolean, message: string | null) =>
    http.put<StoreStatus>("/store/pause", { json: { paused, message } }),
  updateSettings: (prepTimeMinutes: number) =>
    http.put<StoreStatus>("/store/settings", { json: { prep_time_minutes: prepTimeMinutes } }),
};
