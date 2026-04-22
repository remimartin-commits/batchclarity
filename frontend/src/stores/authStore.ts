import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  username: string;
  full_name: string;
  email: string;
  permissions: string[];
  must_change_password: boolean;
  is_mfa_enabled?: boolean;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  hasPermission: (code: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setAuth: (user, accessToken, refreshToken) =>
        set({
          user: {
            ...user,
            permissions: user.permissions ?? [],
            must_change_password: Boolean(user.must_change_password),
          },
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),
      setUser: (user) =>
        set((state) => ({
          user: {
            ...user,
            permissions: user.permissions ?? [],
            must_change_password: Boolean(user.must_change_password),
          },
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
          isAuthenticated: Boolean(state.accessToken),
        })),
      logout: () =>
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
      hasPermission: (code) => get().user?.permissions.includes(code) ?? false,
    }),
    { name: "gmp-auth" }
  )
);
