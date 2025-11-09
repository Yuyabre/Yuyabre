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
  return useMutation<InventoryItem, Error, InventoryItemCreate>({
    mutationFn: (item) => inventoryApi.create(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['inventory', 'low-stock'] });
    },
  });
};

export const useUpdateInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation<InventoryItem, Error, { itemId: string; updates: InventoryItemUpdate }>({
    mutationFn: ({ itemId, updates }) => inventoryApi.update(itemId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
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

