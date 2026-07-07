import { apiClient } from "@/lib/api/client";
import type { DocumentListItem, DocumentOut } from "@/lib/types";

export const documentsApi = {
  list: () => apiClient.get<DocumentListItem[]>("/api/documents"),

  get: (documentId: number) => apiClient.get<DocumentOut>(`/api/documents/${documentId}`),

  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.postForm<{ document: DocumentOut; message: string }>(
      "/api/documents",
      formData
    );
  },

  remove: (documentId: number) => apiClient.delete<void>(`/api/documents/${documentId}`),

  reprocess: (documentId: number) =>
    apiClient.post<DocumentOut>(`/api/documents/${documentId}/reprocess`),
};
