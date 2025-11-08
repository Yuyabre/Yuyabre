import type { InventoryItem, Order, Expense, OrderData, StreamChunk } from '../types';

// Simulate network delay
const delay = (ms = 500): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

// Mock inventory data
const mockInventory: InventoryItem[] = [
  { id: '1', name: 'Milk', category: 'Dairy', quantity: 2, unit: 'liters', threshold: 1, expirationDate: '2025-01-20', shared: true },
  { id: '2', name: 'Eggs', category: 'Dairy', quantity: 6, unit: 'pieces', threshold: 4, expirationDate: '2025-01-18', shared: true },
  { id: '3', name: 'Bread', category: 'Bakery', quantity: 1, unit: 'loaf', threshold: 1, expirationDate: '2025-01-17', shared: true },
  { id: '4', name: 'Tomatoes', category: 'Vegetables', quantity: 8, unit: 'pieces', threshold: 4, expirationDate: '2025-01-19', shared: true },
  { id: '5', name: 'Cheese', category: 'Dairy', quantity: 0.5, unit: 'kg', threshold: 0.2, expirationDate: '2025-01-22', shared: true },
];

// Mock orders data
const mockOrders: Order[] = [
  { id: '1', timestamp: '2025-01-15T10:00:00Z', service: 'Thuisbezorgd', items: [{ name: 'Milk', quantity: 2, price: 3.5 }], total: 3.5, deliveryTime: '2025-01-15T14:00:00Z', status: 'delivered', splitwiseExpenseId: 'exp-1' },
  { id: '2', timestamp: '2025-01-16T09:00:00Z', service: 'Thuisbezorgd', items: [{ name: 'Bread', quantity: 2, price: 2.5 }, { name: 'Eggs', quantity: 12, price: 4.0 }], total: 6.5, deliveryTime: '2025-01-16T13:00:00Z', status: 'delivered', splitwiseExpenseId: 'exp-2' },
  { id: '3', timestamp: '2025-01-17T11:00:00Z', service: 'Thuisbezorgd', items: [{ name: 'Tomatoes', quantity: 10, price: 5.0 }], total: 5.0, deliveryTime: null, status: 'preparing', splitwiseExpenseId: null },
];

// Mock expenses data
const mockExpenses: Expense[] = [
  { id: 'exp-1', description: 'Grocery Order #1', amount: 3.5, splitAmount: 1.75, status: 'settled', orderId: '1', createdAt: '2025-01-15T10:05:00Z' },
  { id: 'exp-2', description: 'Grocery Order #2', amount: 6.5, splitAmount: 3.25, status: 'pending', orderId: '2', createdAt: '2025-01-16T09:05:00Z' },
];

// Inventory API
export const inventoryApi = {
  getAll: async (): Promise<InventoryItem[]> => {
    await delay(300);
    return [...mockInventory];
  },

  getById: async (id: string): Promise<InventoryItem | undefined> => {
    await delay(200);
    return mockInventory.find(item => item.id === id);
  },

  create: async (item: Omit<InventoryItem, 'id' | 'lastUpdated'>): Promise<InventoryItem> => {
    await delay(400);
    const newItem: InventoryItem = {
      id: String(Date.now()),
      ...item,
      lastUpdated: new Date().toISOString(),
    };
    mockInventory.push(newItem);
    return newItem;
  },

  update: async (id: string, updates: Partial<InventoryItem>): Promise<InventoryItem> => {
    await delay(400);
    const index = mockInventory.findIndex(item => item.id === id);
    if (index === -1) throw new Error('Item not found');
    mockInventory[index] = { ...mockInventory[index], ...updates, lastUpdated: new Date().toISOString() };
    return mockInventory[index];
  },

  delete: async (id: string): Promise<{ success: boolean }> => {
    await delay(300);
    const index = mockInventory.findIndex(item => item.id === id);
    if (index === -1) throw new Error('Item not found');
    mockInventory.splice(index, 1);
    return { success: true };
  },

  getLowStock: async (): Promise<InventoryItem[]> => {
    await delay(200);
    return mockInventory.filter(item => item.quantity <= item.threshold);
  },
};

// Orders API
export const ordersApi = {
  getAll: async (): Promise<Order[]> => {
    await delay(300);
    return [...mockOrders];
  },

  getById: async (id: string): Promise<Order | undefined> => {
    await delay(200);
    return mockOrders.find(order => order.id === id);
  },

  create: async (orderData: OrderData): Promise<Order> => {
    await delay(1500); // Simulate order processing
    const newOrder: Order = {
      id: String(Date.now()),
      timestamp: new Date().toISOString(),
      service: 'Thuisbezorgd',
      ...orderData,
      status: 'preparing',
      deliveryTime: null,
      splitwiseExpenseId: null,
    };
    mockOrders.unshift(newOrder);
    return newOrder;
  },

  updateStatus: async (id: string, status: Order['status']): Promise<Order> => {
    await delay(400);
    const order = mockOrders.find(o => o.id === id);
    if (!order) throw new Error('Order not found');
    order.status = status;
    if (status === 'delivered') {
      order.deliveryTime = new Date().toISOString();
    }
    return order;
  },
};

// Expenses API
export const expensesApi = {
  getAll: async (): Promise<Expense[]> => {
    await delay(300);
    return [...mockExpenses];
  },

  getById: async (id: string): Promise<Expense | undefined> => {
    await delay(200);
    return mockExpenses.find(expense => expense.id === id);
  },

  create: async (expenseData: Omit<Expense, 'id' | 'createdAt' | 'status'>): Promise<Expense> => {
    await delay(600);
    const newExpense: Expense = {
      id: `exp-${Date.now()}`,
      createdAt: new Date().toISOString(),
      status: 'pending',
      ...expenseData,
    };
    mockExpenses.unshift(newExpense);
    return newExpense;
  },
};

// Simulate streaming order placement (like AI SDK streaming)
export async function* placeOrderWithStream(orderData: OrderData): AsyncGenerator<StreamChunk, void, unknown> {
  yield { type: 'status', message: 'Processing order...', progress: 0 };
  await delay(300);
  
  yield { type: 'status', message: 'Searching for products...', progress: 25 };
  await delay(400);
  
  yield { type: 'status', message: 'Adding items to cart...', progress: 50 };
  await delay(500);
  
  yield { type: 'status', message: 'Placing order with Thuisbezorgd...', progress: 75 };
  await delay(600);
  
  const order = await ordersApi.create(orderData);
  yield { type: 'order', data: order, progress: 90 };
  
  yield { type: 'status', message: 'Updating inventory...', progress: 95 };
  await delay(300);
  
  yield { type: 'status', message: 'Creating Splitwise expense...', progress: 98 };
  await delay(400);
  
  const expense = await expensesApi.create({
    description: `Grocery Order #${order.id}`,
    amount: order.total,
    splitAmount: order.total / 2, // Mock: split between 2 flatmates
    orderId: order.id,
  });
  
  order.splitwiseExpenseId = expense.id;
  yield { type: 'complete', order, expense, progress: 100 };
}

