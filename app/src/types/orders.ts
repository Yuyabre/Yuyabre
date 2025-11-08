export interface OrderItem {
  name: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: string;
  timestamp: string;
  service: string;
  store: string;
  items: OrderItem[];
  total: number;
  deliveryTime: string | null;
  status: "pending" | "preparing" | "delivering" | "delivered";
  splitwiseExpenseId: string | null;
}

export interface OrderData {
  items: OrderItem[];
  total: number;
}
