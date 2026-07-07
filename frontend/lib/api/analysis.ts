import { apiClient } from "@/lib/api/client";
import type { AnalysisOut, RiskFindingOut } from "@/lib/types";

export const analysisApi = {
  get: (documentId: number) => apiClient.get<AnalysisOut>(`/api/documents/${documentId}/analysis`),

  risks: (documentId: number) =>
    apiClient.get<RiskFindingOut[]>(`/api/documents/${documentId}/risks`),
};
