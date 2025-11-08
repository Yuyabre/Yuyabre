import type { InventoryItem } from "../../types";
import { delay, mockInventory } from "./mocks";

/**
 * Inventory API - CRUD operations for inventory items
 */
export const inventoryApi = {
  getAll: async (): Promise<InventoryItem[]> => {
    await delay(300);
    return [...mockInventory];
  },

  getById: async (id: string): Promise<InventoryItem | undefined> => {
    await delay(200);
    return mockInventory.find((item) => item.id === id);
  },

  create: async (
    item: Omit<InventoryItem, "id" | "lastUpdated">
  ): Promise<InventoryItem> => {
    await delay(400);
    const newItem: InventoryItem = {
      id: String(Date.now()),
      ...item,
      lastUpdated: new Date().toISOString(),
    };
    mockInventory.push(newItem);
    return newItem;
  },

  update: async (
    id: string,
    updates: Partial<InventoryItem>
  ): Promise<InventoryItem> => {
    await delay(400);
    const index = mockInventory.findIndex((item) => item.id === id);
    if (index === -1) throw new Error("Item not found");
    mockInventory[index] = {
      ...mockInventory[index],
      ...updates,
      lastUpdated: new Date().toISOString(),
    };
    return mockInventory[index];
  },

  delete: async (id: string): Promise<{ success: boolean }> => {
    await delay(300);
    const index = mockInventory.findIndex((item) => item.id === id);
    if (index === -1) throw new Error("Item not found");
    mockInventory.splice(index, 1);
    return { success: true };
  },

  getLowStock: async (): Promise<InventoryItem[]> => {
    await delay(200);
    return mockInventory.filter((item) => item.quantity <= item.threshold);
  },
};

