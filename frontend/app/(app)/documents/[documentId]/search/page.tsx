"use client";

import { useState, FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Search as SearchIcon, Sparkles } from "lucide-react";
import { searchApi } from "@/lib/api/search";
import type { SearchResponse } from "@/lib/types";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";

const SUGGESTED_QUERIES = [
  "Show payment terms",
  "Find confidentiality clauses",
  "What are the termination conditions?",
  "Show renewal policy",
];

export default function DocumentSearchPage() {
  const params = useParams<{ documentId: string }>();
  const documentId = Number(params.documentId);
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"retrieve" | "answer">("answer");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  async function runSearch(q: string, searchMode: "retrieve" | "answer" = mode) {
    if (!q.trim()) return;
    setIsSearching(true);
    setQuery(q);
    try {
      const result = await searchApi.search(documentId, q, searchMode);
      setResponse(result);
    } finally {
      setIsSearching(false);
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    runSearch(query);
  }

  return (
    <div>
      <button
        onClick={() => router.push(`/documents/${documentId}`)}
        className="mb-4 flex items-center gap-1.5 text-sm text-ink-faint hover:text-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to document
      </button>

      <PageHeader
        title="Semantic Search"
        description="Ask natural-language questions about this contract, grounded in its actual text."
      />

      <Card className="mb-6">
        <CardContent>
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What are the termination conditions?"
              className="flex-1"
            />
            <Button type="submit" isLoading={isSearching}>
              <SearchIcon className="h-4 w-4" />
              Search
            </Button>
          </form>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-xs text-ink-faint">Mode:</span>
            <button
              onClick={() => setMode("answer")}
              className={`rounded-full border px-3 py-1 text-xs font-medium ${
                mode === "answer"
                  ? "border-accent bg-accent-tint text-accent"
                  : "border-border-strong text-ink-muted"
              }`}
            >
              <Sparkles className="mr-1 inline h-3 w-3" />
              Ask AI
            </button>
            <button
              onClick={() => setMode("retrieve")}
              className={`rounded-full border px-3 py-1 text-xs font-medium ${
                mode === "retrieve"
                  ? "border-accent bg-accent-tint text-accent"
                  : "border-border-strong text-ink-muted"
              }`}
            >
              Quick Search
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {SUGGESTED_QUERIES.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => runSearch(suggestion)}
                className="rounded-full bg-surface-sunken px-3 py-1 text-xs text-ink-muted hover:bg-border"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {isSearching && (
        <p className="text-sm text-ink-faint">Searching document…</p>
      )}

      {response && !isSearching && (
        <div className="space-y-4">
          {response.mode === "answer" && response.answer && (
            <Alert variant="info">
              <span className="font-medium">AI Answer:</span> {response.answer}
            </Alert>
          )}

          {response.results.length === 0 ? (
            <p className="text-sm text-ink-faint">
              No indexed passages found for this query — try a different phrasing.
            </p>
          ) : (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-faint">
                Supporting Passages
              </p>
              <div className="space-y-3">
                {response.results.map((result) => (
                  <Card key={result.chunk_id}>
                    <CardContent>
                      <div className="mb-1 flex items-center justify-between text-xs text-ink-faint">
                        <span>Similarity: {(result.similarity * 100).toFixed(0)}%</span>
                      </div>
                      <p className="whitespace-pre-line text-sm text-ink-muted">{result.text}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
