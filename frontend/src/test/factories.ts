import type { MenuItem } from "@/types/api";

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
