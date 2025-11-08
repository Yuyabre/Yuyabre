import type { User, Group, UserSession } from "../../types/users";
import { delay, mockUser, mockGroup } from "./mocks";

/**
 * User/Group API - User session and group management
 */
export const userApi = {
  getSession: async (): Promise<UserSession> => {
    await delay(300);
    return {
      user: mockUser,
      group: mockGroup,
      token: "mock-token",
    };
  },

  addFlatmate: async (email: string): Promise<Group> => {
    await delay(500);
    const newFlatmate: Group["members"][0] = {
      id: `user-${Date.now()}`,
      name: email.split("@")[0],
      email,
      isAdmin: false,
      joinedAt: new Date().toISOString(),
    };
    mockGroup.members.push(newFlatmate);
    return { ...mockGroup };
  },
};

