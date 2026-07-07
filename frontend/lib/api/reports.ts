import { API_BASE_URL, apiClient, ApiError } from "@/lib/api/client";
import type { ReportFormat, ReportOut } from "@/lib/types";
import { getStoredToken } from "@/lib/auth/token-storage";

export const reportsApi = {
  generate: (documentId: number, format: ReportFormat) =>
    apiClient.post<ReportOut>(`/api/documents/${documentId}/report`, { format }),

  async download(reportId: number, suggestedFilename: string): Promise<void> {
    const token = getStoredToken();
    const response = await fetch(`${API_BASE_URL}/api/documents/reports/${reportId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new ApiError(response.status, {
        error_code: "download_failed",
        message: "Failed to download report",
        detail: null,
      });
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = suggestedFilename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
