import type { Expense } from "../../types";
import { delay, mockExpenses } from "./mocks";

/**
 * Expenses API - Track Splitwise expenses
 */
export const expensesApi = {
  getAll: async (): Promise<Expense[]> => {
    await delay(300);
    return [...mockExpenses];
  },

  getById: async (id: string): Promise<Expense | undefined> => {
    await delay(200);
    return mockExpenses.find((expense) => expense.id === id);
  },

  create: async (
    expenseData: Omit<Expense, "id" | "createdAt" | "status">
  ): Promise<Expense> => {
    await delay(600);
    const newExpense: Expense = {
      id: `exp-${Date.now()}`,
      createdAt: new Date().toISOString(),
      status: "pending",
      ...expenseData,
    };
    mockExpenses.unshift(newExpense);
    return newExpense;
  },
};

