"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import type { Document, User } from "@/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type Toast = {
  tone: "success" | "error";
  message: string;
};

type Props = {
  documentId: string;
};

export default function DocumentDetailPage({ documentId }: Props) {
  const router = useRouter();
  const [document, setDocument] = useState<Document | null>(null);
  const [currentUser] = useState<User | null>(() => {
    if (typeof window === "undefined") {
      return null;
    }

    const storedUser = window.localStorage.getItem("current_user");
    return storedUser ? (JSON.parse(storedUser) as User) : null;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSigning, setIsSigning] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);
  const [error, setError] = useState("");

  const pdfUrl = document?.file_url
    ? document.file_url.startsWith("http")
      ? document.file_url
      : `${API_URL}${document.file_url}`
    : "";

  const latestSignature = document?.signatures?.[document.signatures.length - 1];
  const canReview =
    currentUser?.role === "dean" &&
    document?.status === "pending" &&
    document?.recipient_id === currentUser.id;

  const loadDocument = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/v1/documents/${documentId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load document.");
      }

      setDocument((await response.json()) as Document);
    } catch {
      setError("Unable to load document.");
    } finally {
      setIsLoading(false);
    }
  }, [documentId, router]);

  useEffect(() => {
    queueMicrotask(() => {
      void loadDocument();
    });
  }, [loadDocument]);

  async function handleAction(action: "sign" | "reject") {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    setToast(null);
    setError("");

    if (action === "sign") {
      setIsSigning(true);
    } else {
      setIsRejecting(true);
    }

    try {
      const response = await fetch(
        `${API_URL}/api/v1/documents/${documentId}/${action}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error("Review action failed.");
      }

      setDocument((await response.json()) as Document);
      setToast({
        tone: "success",
        message:
          action === "sign"
            ? "Document signed successfully."
            : "Document rejected.",
      });
    } catch {
      setToast({
        tone: "error",
        message: "Unable to update document status.",
      });
    } finally {
      setIsSigning(false);
      setIsRejecting(false);
    }
  }

  if (isLoading) {
    return (
      <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-gray-200 bg-white p-5 text-sm text-gray-600 shadow-sm">
          Loading document...
        </div>
      </section>
    );
  }

  if (error || !document) {
    return (
      <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">
          {error || "Document not found."}
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-950">{document.title}</h1>
          <p className="mt-2 text-sm capitalize text-gray-600">
            Status: {document.status}
          </p>
        </div>

        {document.status === "signed" ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 shadow-sm">
            <p className="font-semibold">Signed Digitally</p>
            {latestSignature ? (
              <p className="mt-1 text-xs">
                Signature #{latestSignature.id.slice(0, 8)} ·{" "}
                {new Date(latestSignature.signed_at).toLocaleString()}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>

      {toast ? (
        <div
          className={`mb-5 rounded-md px-4 py-3 text-sm ${
            toast.tone === "success"
              ? "bg-emerald-50 text-emerald-800"
              : "bg-red-50 text-red-700"
          }`}
        >
          {toast.message}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        {pdfUrl ? (
          <iframe
            title={document.title}
            src={pdfUrl}
            className="h-[72vh] w-full bg-gray-100"
          />
        ) : (
          <div className="p-5 text-sm text-gray-600">
            This document does not have a PDF file attached.
          </div>
        )}
      </div>

      {canReview ? (
        <div className="sticky bottom-0 mt-6 border-t border-gray-200 bg-gray-50/95 py-4 backdrop-blur">
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={() => void handleAction("reject")}
              disabled={isRejecting || isSigning}
              className="rounded-md bg-red-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {isRejecting ? "Rejecting..." : "Reject"}
            </button>
            <button
              type="button"
              onClick={() => void handleAction("sign")}
              disabled={isSigning || isRejecting}
              className="rounded-md bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {isSigning ? "Signing..." : "Approve & Sign"}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
