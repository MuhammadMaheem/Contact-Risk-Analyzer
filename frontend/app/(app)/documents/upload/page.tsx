"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { documentsApi } from "@/lib/api/documents";
import { ApiError } from "@/lib/api/client";
import { PageHeader } from "@/components/layout/page-header";
import { UploadDropzone } from "@/components/documents/upload-dropzone";
import { Card, CardContent } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";

export default function UploadPage() {
  const router = useRouter();
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setIsUploading(true);
    setError(null);
    try {
      const { document } = await documentsApi.upload(file);
      router.push(`/documents/${document.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
      setIsUploading(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Upload Document"
        description="Upload a contract or legal document to start AI risk analysis."
      />

      <Card className="max-w-2xl">
        <CardContent>
          {error && (
            <Alert variant="error" className="mb-4">
              {error}
            </Alert>
          )}
          <UploadDropzone onFileSelected={handleFile} disabled={isUploading} />
          {isUploading && (
            <p className="mt-4 text-center text-sm text-ink-faint">
              Uploading and starting AI analysis…
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
