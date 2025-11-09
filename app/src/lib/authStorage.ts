import type { Household, User } from "@/types/users";

const USER_STORAGE_KEY = "yuyabre.auth.user";
const HOUSEHOLD_STORAGE_KEY = "yuyabre.auth.household";

export const authStorage = {
  loadUser(): User | null {
    const raw = window.localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch (error) {
      console.warn("Failed to parse stored user", error);
      return null;
    }
  },

  saveUser(user: User | null): void {
    if (!user) {
      window.localStorage.removeItem(USER_STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  },

  loadHousehold(): Household | null {
    const raw = window.localStorage.getItem(HOUSEHOLD_STORAGE_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as Household;
    } catch (error) {
      console.warn("Failed to parse stored household", error);
      return null;
    }
  },

  saveHousehold(household: Household | null): void {
    if (!household) {
      window.localStorage.removeItem(HOUSEHOLD_STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(
      HOUSEHOLD_STORAGE_KEY,
      JSON.stringify(household)
    );
  },

  clear(): void {
    window.localStorage.removeItem(USER_STORAGE_KEY);
    window.localStorage.removeItem(HOUSEHOLD_STORAGE_KEY);
  },
};

export const AUTH_USER_STORAGE_KEY = USER_STORAGE_KEY;
export const AUTH_HOUSEHOLD_STORAGE_KEY = HOUSEHOLD_STORAGE_KEY;

