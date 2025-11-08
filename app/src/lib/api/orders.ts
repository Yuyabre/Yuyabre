import type { Order, OrderData } from "../../types/orders";
import type { StreamChunk } from "../../types";
import { delay, mockOrders } from "./mocks";
import { expensesApi } from "./expenses";

/**
 * Orders API - Create and track orders
 */
export const ordersApi = {
  getAll: async (): Promise<Order[]> => {
    await delay(300);
    return [...mockOrders];
  },

  getById: async (id: string): Promise<Order | undefined> => {
    await delay(200);
    return mockOrders.find((order) => order.id === id);
  },

  create: async (orderData: OrderData): Promise<Order> => {
    await delay(1500); // Simulate order processing
    const newOrder: Order = {
      id: String(Date.now()),
      timestamp: new Date().toISOString(),
      service: "Thuisbezorgd",
      store: "Albert Heijn", // Default store, can be overridden
      ...orderData,
      status: "preparing",
      deliveryTime: null,
      splitwiseExpenseId: null,
    };
    mockOrders.unshift(newOrder);
    return newOrder;
  },

  updateStatus: async (id: string, status: Order["status"]): Promise<Order> => {
    await delay(400);
    const order = mockOrders.find((o) => o.id === id);
    if (!order) throw new Error("Order not found");
    order.status = status;
    if (status === "delivered") {
      order.deliveryTime = new Date().toISOString();
    }
    return order;
  },

  approve: async (
    id: string,
    orderData?: Omit<
      Order,
      "id" | "timestamp" | "status" | "deliveryTime" | "splitwiseExpenseId"
    >
  ): Promise<{ order: Order; message: string }> => {
    await delay(800); // Simulate API call delay
    let order = mockOrders.find((o) => o.id === id);

    // If order doesn't exist in mockOrders but orderData is provided, create it
    if (!order && orderData) {
      order = {
        id,
        timestamp: new Date().toISOString(),
        status: "pending",
        deliveryTime: null,
        splitwiseExpenseId: null,
        ...orderData,
      };
      mockOrders.unshift(order);
    }

    if (!order) {
      throw new Error("Order not found");
    }

    if (order.status !== "pending") {
      throw new Error(
        `Order cannot be approved. Current status: ${order.status}`
      );
    }

    // Update order status to preparing
    order.status = "preparing";

    // Create expense for the order
    const expense = await expensesApi.create({
      description: `Grocery Order #${order.id}`,
      amount: order.total,
      splitAmount: order.total / 2, // Mock: split between 2 flatmates
      orderId: order.id,
    });

    order.splitwiseExpenseId = expense.id;

    const message = `Your order has been approved and is now being prepared! The order will be delivered in approximately 30-45 minutes. A Splitwise expense has been created for €${order.total.toFixed(
      2
    )}.`;

    return { order, message };
  },
};

/**
 * Simulate streaming order placement (like AI SDK streaming)
 */
export async function* placeOrderWithStream(
  orderData: OrderData
): AsyncGenerator<StreamChunk, void, unknown> {
  yield { type: "status", message: "Processing order...", progress: 0 };
  await delay(300);

  yield { type: "status", message: "Searching for products...", progress: 25 };
  await delay(400);

  yield { type: "status", message: "Adding items to cart...", progress: 50 };
  await delay(500);

  yield {
    type: "status",
    message: "Placing order with Thuisbezorgd...",
    progress: 75,
  };
  await delay(600);

  const order = await ordersApi.create(orderData);
  yield { type: "order", data: order, progress: 90 };

  yield { type: "status", message: "Updating inventory...", progress: 95 };
  await delay(300);

  yield {
    type: "status",
    message: "Creating Splitwise expense...",
    progress: 98,
  };
  await delay(400);

  const expense = await expensesApi.create({
    description: `Grocery Order #${order.id}`,
    amount: order.total,
    splitAmount: order.total / 2, // Mock: split between 2 flatmates
    orderId: order.id,
  });

  order.splitwiseExpenseId = expense.id;
  yield { type: "complete", order, expense, progress: 100 };
}

