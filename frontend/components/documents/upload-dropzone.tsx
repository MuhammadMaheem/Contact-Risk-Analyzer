"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileText } from "lucide-react";
import { cn } from "@/lib/utils/cn";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"];
const MAX_SIZE_BYTES = 20 * 1024 * 1024;

export function UploadDropzone({
  onFileSelected,
  disabled,
}: {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndEmit = useCallback(
    (file: File) => {
      const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
      if (!ALLOWED_EXTENSIONS.includes(extension)) {
        setError(`Unsupported file type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
        return;
      }
      if (file.size > MAX_SIZE_BYTES) {
        setError("File exceeds the 20MB upload limit.");
        return;
      }
      setError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragActive(true);
        }}
        onDragLeave={() => setIsDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragActive(false);
          const file = e.dataTransfer.files?.[0];
          if (file) validateAndEmit(file);
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-16 text-center transition-colors",
          isDragActive ? "border-accent bg-accent-tint/40" : "border-border-strong bg-surface-sunken/50",
          disabled && "cursor-not-allowed opacity-60"
        )}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-tint text-accent">
          <UploadCloud className="h-6 w-6" />
        </div>
        <div>
          <p className="font-medium text-ink">Drag & drop your contract here</p>
          <p className="mt-1 text-sm text-ink-faint">or click to browse — PDF, DOCX, or TXT, up to 20MB</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-ink-faint">
          <FileText className="h-3.5 w-3.5" />
          {ALLOWED_EXTENSIONS.join(" · ")}
        </div>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept={ALLOWED_EXTENSIONS.join(",")}
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) validateAndEmit(file);
            e.target.value = "";
          }}
        />
      </div>
      {error && <p className="mt-2 text-sm text-danger">{error}</p>}
    </div>
  );
}
