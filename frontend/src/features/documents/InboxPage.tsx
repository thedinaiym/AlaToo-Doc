"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import type { Document } from "@/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function InboxPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    async function loadInbox() {
      try {
        const response = await fetch(`${API_URL}/api/v1/documents/inbox`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to load inbox.");
        }

        setDocuments((await response.json()) as Document[]);
      } catch {
        setError("Unable to load inbox documents.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadInbox();
  }, [router]);

  return (
    <section className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-950">Inbox</h1>
        <p className="mt-2 text-sm text-gray-600">Pending applications for review.</p>
      </div>

      {error ? (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        {isLoading ? (
          <div className="p-5 text-sm text-gray-600">Loading...</div>
        ) : documents.length === 0 ? (
          <div className="p-5 text-sm text-gray-600">No pending applications.</div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {documents.map((document) => (
              <li key={document.id} className="p-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-gray-950">{document.title}</p>
                    <p className="mt-1 text-sm capitalize text-gray-600">
                      {document.status}
                    </p>
                  </div>
                  <Link
                    href={`/dashboard/documents/${document.id}`}
                    className="rounded-md bg-blue-700 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-800"
                  >
                    Review
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
