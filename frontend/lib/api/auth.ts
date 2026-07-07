import { apiClient } from "@/lib/api/client";
import type { UserProfile } from "@/lib/types";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const authApi = {
  register: (email: string, password: string, fullName: string) =>
    apiClient.post<UserProfile>("/api/auth/register", {
      email,
      password,
      full_name: fullName,
    }),

  login: (email: string, password: string) =>
    apiClient.post<TokenResponse>("/api/auth/login", { email, password }),

  me: () => apiClient.get<UserProfile>("/api/auth/me"),

  updateProfile: (payload: {
    full_name?: string;
    current_password?: string;
    new_password?: string;
  }) => apiClient.patch<UserProfile>("/api/auth/me", payload),
};
