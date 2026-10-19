import type { MenuItem, Order } from "@/types/api";

export function menuItem(overrides: Partial<MenuItem> = {}): MenuItem {
  return {
    id: 1,
    name: "Cali Clássico",
    description: null,
    price: "29.90",
    image_url: null,
    category: { id: 1, name: "Hambúrgueres" },
    is_paused: false,
    portions: 10,
    availability: "available",
    recipe: null,
    ...overrides,
  };
}

export function order(overrides: Partial<Order> = {}): Order {
  return {
    id: 42,
    status: "awaiting_acceptance",
    fulfillment: "delivery",
    status_since: "2026-10-19T15:00:00Z",
    customer_id: 1,
    customer_name: "João Silva",
    delivery_address: "Rua A, 1",
    total: "22.00",
    created_at: "2026-10-19T15:00:00Z",
    updated_at: "2026-10-19T15:00:00Z",
    items: [],
    payment: null,
    status_reason: null,
    events: null,
    available_actions: [],
    ...overrides,
  };
}
