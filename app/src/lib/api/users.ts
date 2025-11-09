import { delay, mockUser } from "./mocks";

/**
 * User/Group API - User session and group management
 * Note: These functions are currently unused and may be implemented in the future
 */
export const userApi = {
  // Placeholder for future implementation
  getSession: async () => {
    await delay(300);
    return {
      user: mockUser,
      token: "mock-token",
    };
  },
};

