import type { InventoryItem, Expense } from "../../types";
import type { Order } from "../../types/orders";
import type { User } from "../../types/users";

// Simulate network delay
export const delay = (ms = 500): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

// Mock inventory data
export const mockInventory: InventoryItem[] = [
  {
    item_id: "1",
    name: "Milk",
    category: "Dairy",
    quantity: 2,
    unit: "liters",
    threshold: 1,
    expiration_date: "2025-01-20",
    shared: true,
    last_updated: new Date().toISOString(),
  },
  {
    item_id: "2",
    name: "Eggs",
    category: "Dairy",
    quantity: 6,
    unit: "pieces",
    threshold: 4,
    expiration_date: "2025-01-18",
    shared: true,
    last_updated: new Date().toISOString(),
  },
  {
    item_id: "3",
    name: "Bread",
    category: "Bakery",
    quantity: 1,
    unit: "loaf",
    threshold: 1,
    expiration_date: "2025-01-17",
    shared: true,
    last_updated: new Date().toISOString(),
  },
  {
    item_id: "4",
    name: "Tomatoes",
    category: "Vegetables",
    quantity: 8,
    unit: "pieces",
    threshold: 4,
    expiration_date: "2025-01-19",
    shared: true,
    last_updated: new Date().toISOString(),
  },
  {
    item_id: "5",
    name: "Cheese",
    category: "Dairy",
    quantity: 0.5,
    unit: "kg",
    threshold: 0.2,
    expiration_date: "2025-01-22",
    shared: true,
    last_updated: new Date().toISOString(),
  },
];

// Mock orders data
export const mockOrders: Order[] = [
  {
    id: "1",
    timestamp: "2025-01-15T10:00:00Z",
    service: "Thuisbezorgd",
    store: "Albert Heijn",
    items: [{ name: "Milk", quantity: 2, price: 3.5 }],
    total: 3.5,
    deliveryTime: "2025-01-15T14:00:00Z",
    status: "delivered",
    splitwiseExpenseId: "exp-1",
  },
  {
    id: "2",
    timestamp: "2025-01-16T09:00:00Z",
    service: "Thuisbezorgd",
    store: "Jumbo",
    items: [
      { name: "Bread", quantity: 2, price: 2.5 },
      { name: "Eggs", quantity: 12, price: 4.0 },
    ],
    total: 6.5,
    deliveryTime: "2025-01-16T13:00:00Z",
    status: "delivered",
    splitwiseExpenseId: "exp-2",
  },
  {
    id: "3",
    timestamp: "2025-01-17T11:00:00Z",
    service: "Thuisbezorgd",
    store: "Albert Heijn",
    items: [{ name: "Tomatoes", quantity: 10, price: 5.0 }],
    total: 5.0,
    deliveryTime: null,
    status: "preparing",
    splitwiseExpenseId: null,
  },
];

// Mock expenses data
export const mockExpenses: Expense[] = [
  {
    id: "exp-1",
    description: "Grocery Order #1",
    amount: 3.5,
    splitAmount: 1.75,
    status: "settled",
    orderId: "1",
    createdAt: "2025-01-15T10:05:00Z",
  },
  {
    id: "exp-2",
    description: "Grocery Order #2",
    amount: 6.5,
    splitAmount: 3.25,
    status: "pending",
    orderId: "2",
    createdAt: "2025-01-16T09:05:00Z",
  },
];

// Mock user data
export const mockUser: User = {
  user_id: "user-1",
  name: "John Doe",
  email: "john@example.com",
  is_active: true,
  joined_date: "2024-01-01T00:00:00Z",
};

