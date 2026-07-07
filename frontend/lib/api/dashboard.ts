import { apiClient } from "@/lib/api/client";
import type { DashboardStats } from "@/lib/types";

export const dashboardApi = {
  stats: () => apiClient.get<DashboardStats>("/api/dashboard/stats"),
};
