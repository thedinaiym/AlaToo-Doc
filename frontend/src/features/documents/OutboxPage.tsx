"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import type { Document } from "@/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function OutboxPage() {
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

    async function loadOutbox() {
      try {
        const response = await fetch(`${API_URL}/api/v1/documents/outbox`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to load outbox.");
        }

        setDocuments((await response.json()) as Document[]);
      } catch {
        setError("Unable to load outbox documents.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadOutbox();
  }, [router]);

  return (
    <section className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-950">Outbox</h1>
          <p className="mt-2 text-sm text-gray-600">Applications you submitted.</p>
        </div>
        <Link
          href="/dashboard/create"
          className="rounded-md bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800"
        >
          Create
        </Link>
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
          <div className="p-5 text-sm text-gray-600">No submitted applications yet.</div>
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
                    className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
                  >
                    Open
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
