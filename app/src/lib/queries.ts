import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi, ordersApi, expensesApi } from './api';
import type { InventoryItem, Order, Expense, OrderData } from '../types';

// Inventory queries
export const useInventory = () => {
  return useQuery<InventoryItem[]>({
    queryKey: ['inventory'],
    queryFn: () => inventoryApi.getAll(),
  });
};

export const useLowStockItems = () => {
  return useQuery<InventoryItem[]>({
    queryKey: ['inventory', 'low-stock'],
    queryFn: () => inventoryApi.getLowStock(),
  });
};

export const useCreateInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation<InventoryItem, Error, Omit<InventoryItem, 'id' | 'lastUpdated'>>({
    mutationFn: (item) => inventoryApi.create(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

export const useUpdateInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation<InventoryItem, Error, { id: string; updates: Partial<InventoryItem> }>({
    mutationFn: ({ id, updates }) => inventoryApi.update(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

export const useDeleteInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation<{ success: boolean }, Error, string>({
    mutationFn: (id) => inventoryApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

// Orders queries
export const useOrders = () => {
  return useQuery<Order[]>({
    queryKey: ['orders'],
    queryFn: () => ordersApi.getAll(),
  });
};

export const useCreateOrder = () => {
  const queryClient = useQueryClient();
  return useMutation<Order, Error, OrderData>({
    mutationFn: (orderData) => ordersApi.create(orderData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
    },
  });
};

// Expenses queries
export const useExpenses = () => {
  return useQuery<Expense[]>({
    queryKey: ['expenses'],
    queryFn: () => expensesApi.getAll(),
  });
};

