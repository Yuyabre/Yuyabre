import { create } from "zustand";
import type { ViewId } from "../types";
import type { IMessage } from "@/types/chat";

interface Store {
  // Chat state
  messages: IMessage[];
  addMessage: (message: IMessage) => void;
  clearMessages: () => void;

  // Sidebar state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Active view
  activeView: ViewId;
  setActiveView: (view: ViewId) => void;
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

  // Active view
  activeView: "chat",
  setActiveView: (view) => set({ activeView: view }),
}));

export { useStore };
