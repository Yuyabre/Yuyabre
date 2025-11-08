import { create } from "zustand";
import type { IMessage } from "@/types/chat";
import type { User, Group } from "@/types/users";

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
  currentGroup: Group | null;
  setCurrentUser: (user: User | null) => void;
  setCurrentGroup: (group: Group | null) => void;
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
  currentGroup: null,
  setCurrentUser: (user) => set({ currentUser: user }),
  setCurrentGroup: (group) => set({ currentGroup: group }),
}));

export { useStore };
