import { apiClient } from "@/lib/api/client";
import type {
  AdminUserOut,
  AuditLogOut,
  DocumentListItem,
  SystemStatsOut,
  UserRole,
} from "@/lib/types";

export const adminApi = {
  users: () => apiClient.get<AdminUserOut[]>("/api/admin/users"),

  updateUser: (userId: number, payload: { role?: UserRole; is_active?: boolean }) =>
    apiClient.patch<AdminUserOut>(`/api/admin/users/${userId}`, payload),

  documents: () => apiClient.get<DocumentListItem[]>("/api/admin/documents"),

  logs: (level?: string) =>
    apiClient.get<AuditLogOut[]>(`/api/admin/logs${level ? `?level=${level}` : ""}`),

  stats: () => apiClient.get<SystemStatsOut>("/api/admin/stats"),
};
