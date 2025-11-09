import {
  useQuery,
  useMutation,
  useQueryClient,
  useQueries,
} from '@tanstack/react-query';
import { inventoryApi, ordersApi, expensesApi, authApi } from "./api";
import type {
  CreateHouseholdRequest,
  Household,
  JoinHouseholdRequest,
  LoginRequest,
  SignupRequest,
  User,
} from "../types/users";
import type { InventoryItem, InventoryItemCreate, InventoryItemUpdate, Expense } from "../types";
import type { Order, OrderData } from "../types/orders";

// Inventory queries
// Note: useInventory now uses the current user's ID from the store
// For viewing other users' inventory, use useUserInventory directly
export const useInventory = () => {
  // This will be handled by InventoryModal which gets currentUser from store
  // For now, return empty array - InventoryModal will use useUserInventory directly
  return useQuery<InventoryItem[]>({
    queryKey: ['inventory'],
    queryFn: () => Promise.resolve([]),
    enabled: false,
  });
};

export const useLowStockItems = () => {
  return useQuery<InventoryItem[]>({
    queryKey: ['inventory', 'low-stock'],
    queryFn: () => inventoryApi.getLowStock(),
  });
};

export const useUserInventory = (userId: string | null) => {
  return useQuery<InventoryItem[]>({
    queryKey: ['inventory', 'user', userId],
    queryFn: () => (userId ? inventoryApi.getByUserId(userId) : []),
    enabled: !!userId,
  });
};

export const useCreateInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation<
    InventoryItem,
    Error,
    { userId: string; item: InventoryItemCreate }
  >({
    mutationFn: ({ userId, item }) => inventoryApi.create(userId, item),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({
        queryKey: ['inventory', 'user', variables.userId],
      });
      queryClient.invalidateQueries({ queryKey: ['inventory', 'low-stock'] });
    },
  });
};

export const useUpdateInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation<
    InventoryItem,
    Error,
    { userId: string; itemId: string; updates: InventoryItemUpdate }
  >({
    mutationFn: ({ userId, itemId, updates }) =>
      inventoryApi.update(userId, itemId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({
        queryKey: ['inventory', 'user', variables.userId],
      });
      queryClient.invalidateQueries({ queryKey: ['inventory', 'low-stock'] });
    },
  });
};

export const useDeleteInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (itemId) => inventoryApi.delete(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['inventory', 'low-stock'] });
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

// Auth mutations
export const useSignup = () => {
  return useMutation<User, Error, SignupRequest>({
    mutationFn: (payload) => authApi.signup(payload),
  });
};

export const useLogin = () => {
  return useMutation<User, Error, LoginRequest>({
    mutationFn: (payload) => authApi.login(payload),
  });
};

export const useCreateHousehold = () => {
  return useMutation<Household, Error, { userId: string; data: CreateHouseholdRequest }>({
    mutationFn: ({ userId, data }) => authApi.createHousehold(userId, data),
  });
};

export const useJoinHousehold = () => {
  const queryClient = useQueryClient();
  return useMutation<void, Error, { userId: string; data: JoinHouseholdRequest }>({
    mutationFn: ({ userId, data }) => authApi.joinHousehold(userId, data).then(() => undefined),
    onSuccess: (_, variables) => {
      // Refetch user to get updated household_id
      queryClient.invalidateQueries({ queryKey: ['user', variables.userId] });
    },
  });
};

export const useGetUser = (userId: string | null) => {
  return useQuery<User | null>({
    queryKey: ['user', userId],
    queryFn: () => (userId ? authApi.getUser(userId) : null),
    enabled: !!userId,
  });
};

export const useGetHousehold = (householdId: string | null) => {
  return useQuery<Household | null>({
    queryKey: ['household', householdId],
    queryFn: () => (householdId ? authApi.getHousehold(householdId) : null),
    enabled: !!householdId,
  });
};

export const useHouseholdMembers = (memberIds: string[]) => {
  const uniqueIds = Array.from(new Set(memberIds.filter(Boolean)));

  const results = useQueries({
    queries: uniqueIds.map((id) => ({
      queryKey: ['user', id],
      queryFn: () => authApi.getUser(id),
      enabled: Boolean(id),
      staleTime: 1000 * 60 * 5,
    })),
  });

  const isLoading = results.some((result) => result.isLoading);
  const isError = results.some((result) => result.isError);
  const members = results
    .map((result) => result.data)
    .filter((member): member is User => Boolean(member));

  return { members, isLoading, isError };
};

