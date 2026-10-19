// Contratos da API (espelham os schemas Pydantic do backend).
// Valores monetários chegam como string decimal ("22.90") para não perder precisão.

export type Role = "customer" | "manager" | "cook";
export type Sex = "male" | "female" | "other";

export type OrderStatus =
  | "awaiting_acceptance"
  | "in_preparation"
  | "out_for_delivery"
  | "completed"
  | "cancelled"
  | "rejected";

export type OrderAction = "accept" | "reject" | "dispatch" | "cancel" | "complete";
export type Availability = "available" | "low" | "sold_out" | "paused";
export type StockLevel = "ok" | "low" | "out";
export type Money = string;

export interface User {
  id: number;
  role: Role;
  name: string;
  first_name: string;
  username: string | null;
  email: string;
}

export interface Address {
  state: string;
  city: string;
  district: string;
  street: string;
}

export interface Profile extends User {
  cpf: string;
  birth_date: string;
  sex: Sex | null;
  address: Address | null;
}

export interface SessionResponse {
  user: User;
}

export interface Category {
  id: number;
  name: string;
}

export interface RecipeLine {
  ingredient_id: number;
  ingredient_name: string;
  quantity: number;
  in_stock: number;
}

export interface MenuItem {
  id: number;
  name: string;
  description: string | null;
  price: Money;
  image_url: string | null;
  category: Category;
  is_paused: boolean;
  portions: number | null;
  availability: Availability;
  recipe: RecipeLine[] | null;
}

export interface MenuItemInput {
  name: string;
  description: string | null;
  price: string;
  category_id: number;
  recipe: { ingredient_id: number; quantity: number }[];
}

export interface Ingredient {
  id: number;
  name: string;
  quantity: number;
  used_in: number;
  level: StockLevel;
  updated_at: string;
}

export interface Inventory {
  items: Ingredient[];
  low_stock_threshold: number;
}

export interface IngredientAddResult {
  ingredient: Ingredient;
  created: boolean;
  added: number;
}

export interface OrderItem {
  id: number;
  menu_item_id: number | null;
  product_name: string;
  unit_price: Money;
  quantity: number;
  subtotal: Money;
  notes: string | null;
}

export interface OrderEvent {
  from_status: OrderStatus | null;
  to_status: OrderStatus;
  actor_name: string | null;
  created_at: string;
}

export interface Order {
  id: number;
  status: OrderStatus;
  customer_id: number | null;
  customer_name: string;
  delivery_address: string | null;
  total: Money;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  payment: { method: "pix"; amount: Money; paid_at: string } | null;
  events: OrderEvent[] | null;
  available_actions: OrderAction[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface OrderFilters {
  status?: OrderStatus[];
  start?: string;
  end?: string;
  q?: string;
  page?: number;
  page_size?: number;
  sort?: "newest" | "oldest";
}

export interface OrderActionResult {
  order: Order;
  message: string;
}

export interface SalesReport {
  start: string | null;
  end: string | null;
  low_stock_threshold: number;
  summary: { revenue: Money; orders: number; items_sold: number; average_ticket: Money };
  daily: { date: string; orders: number; revenue: Money }[];
  top_products: { product_name: string; quantity: number; total: Money }[];
  sales_by_day: {
    date: string;
    product_name: string;
    quantity: number;
    unit_price: Money;
    total: Money;
  }[];
  ingredients_used: { ingredient_id: number; name: string; quantity: number }[];
  ingredients_to_buy: { ingredient_id: number; name: string; quantity: number }[];
}

export interface StaffMember {
  id: number;
  role: Role;
  name: string;
  cpf: string;
  email: string;
  birth_date: string;
  sex: Sex | null;
  created_at: string;
}

export interface ApiErrorBody {
  error: { code: string; message: string; fields: Record<string, string> };
}

export interface OpeningHour {
  weekday: number; // 0 = segunda … 6 = domingo
  opens_at: string; // "HH:MM:SS"
  closes_at: string;
}

export interface StoreStatus {
  accepting_orders: boolean;
  within_hours: boolean;
  is_paused: boolean;
  pause_message: string | null;
  message: string | null;
  next_opening_at: string | null;
  hours: OpeningHour[];
  prep_time_minutes: number;
}
