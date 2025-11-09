import { create } from "zustand";
import type { IMessage } from "@/types/chat";
import type { User, Household } from "@/types/users";

interface Store {
  // Chat state
  messages: IMessage[];
  addMessage: (message: IMessage) => void;
  clearMessages: () => void;

  // Sidebar state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // User and group state
  currentUser: User | null;
  currentHousehold: Household | null;
  setCurrentUser: (user: User | null) => void;
  setCurrentHousehold: (household: Household | null) => void;
}

const useStore = create<Store>((set) => ({
  // Chat state
  messages: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  clearMessages: () => set({ messages: [] }),

  // Sidebar state
  sidebarCollapsed: false,
  toggleSidebar: () =>
    set((state) => ({
      sidebarCollapsed: !state.sidebarCollapsed,
    })),

  // User and group state
  currentUser: null,
  currentHousehold: null,
  setCurrentUser: (user) => set({ currentUser: user }),
  setCurrentHousehold: (household) => set({ currentHousehold: household }),
}));

export { useStore };
