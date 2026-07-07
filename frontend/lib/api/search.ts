import { apiClient } from "@/lib/api/client";
import type { SearchResponse } from "@/lib/types";

export const searchApi = {
  search: (documentId: number, query: string, mode: "retrieve" | "answer", topK = 5) =>
    apiClient.post<SearchResponse>(`/api/documents/${documentId}/search`, {
      query,
      mode,
      top_k: topK,
    }),
};
