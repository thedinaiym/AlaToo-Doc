"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import type { User } from "@/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type CurrentUser = User | null;

export default function CreateDocumentPage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [recipientId, setRecipientId] = useState("");
  const [reason, setReason] = useState("");
  const [generatedText, setGeneratedText] = useState("");
  const [deans, setDeans] = useState<User[]>([]);
  const [currentUser] = useState<CurrentUser>(() => {
    if (typeof window === "undefined") {
      return null;
    }

    const storedUser = window.localStorage.getItem("current_user");
    return storedUser ? (JSON.parse(storedUser) as User) : null;
  });
  const [isLoadingDeans, setIsLoadingDeans] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const selectedDean = useMemo(
    () => deans.find((dean) => dean.id === recipientId),
    [deans, recipientId],
  );

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.replace("/login");
      return;
    }

    async function loadDeans() {
      try {
        const response = await fetch(`${API_URL}/api/v1/users?role=dean`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to load recipients.");
        }

        const users = (await response.json()) as User[];
        setDeans(users);
        setRecipientId(users[0]?.id ?? "");
      } catch {
        setError("Unable to load dean recipients.");
      } finally {
        setIsLoadingDeans(false);
      }
    }

    void loadDeans();
  }, [router]);

  async function handleGenerateWithAi() {
    setError("");

    if (!topic.trim() || !recipientId || !reason.trim()) {
      setError("Fill in the topic, recipient dean, and reason first.");
      return;
    }

    setIsGenerating(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/documents/predict-text`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          student_name: currentUser?.full_name ?? "Student",
          faculty: "General",
          recipient_title: selectedDean?.full_name ?? "Dean",
          reason: `Topic: ${topic}\n${reason}`,
        }),
      });

      if (!response.ok) {
        throw new Error("AI generation failed.");
      }

      const data = (await response.json()) as { generated_text: string };
      setGeneratedText(data.generated_text);
    } catch {
      setError("Unable to generate text with AI.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    if (!topic.trim() || !recipientId || !generatedText.trim()) {
      setError("Complete the form and application text before submitting.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/documents/create`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: topic,
          raw_text: generatedText,
          recipient_id: recipientId,
        }),
      });

      if (!response.ok) {
        throw new Error("Application submission failed.");
      }

      router.push("/dashboard/outbox");
      router.refresh();
    } catch {
      setError("Unable to submit application.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-950">Create Application</h1>
        <p className="mt-2 text-sm text-gray-600">
          Draft, review, and submit a university application for approval.
        </p>
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase text-blue-700">Step 1</p>
          <p className="mt-1 text-sm font-medium text-gray-950">Application details</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-3">
          <p className="text-xs font-semibold uppercase text-gray-500">Step 2</p>
          <p className="mt-1 text-sm font-medium text-gray-950">Review and submit</p>
        </div>
      </div>

      <form className="space-y-6" onSubmit={handleSubmit}>
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label htmlFor="topic" className="block text-sm font-medium text-gray-800">
                Topic
              </label>
              <input
                id="topic"
                value={topic}
                onChange={(event) => setTopic(event.target.value)}
                className="mt-2 block w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                placeholder="Application topic"
                required
              />
            </div>

            <div>
              <label
                htmlFor="recipient"
                className="block text-sm font-medium text-gray-800"
              >
                Recipient Dean
              </label>
              <select
                id="recipient"
                value={recipientId}
                onChange={(event) => setRecipientId(event.target.value)}
                disabled={isLoadingDeans}
                className="mt-2 block w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100"
                required
              >
                {isLoadingDeans ? (
                  <option value="">Loading deans...</option>
                ) : (
                  <>
                    <option value="">Select dean</option>
                    {deans.map((dean) => (
                      <option key={dean.id} value={dean.id}>
                        {dean.full_name}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>
          </div>

          <div className="mt-5">
            <label htmlFor="reason" className="block text-sm font-medium text-gray-800">
              Reason/Details
            </label>
            <textarea
              id="reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className="mt-2 min-h-32 block w-full resize-y rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm leading-6 text-gray-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              placeholder="Describe the reason for this application"
              required
            />
          </div>

          <div className="mt-5 flex justify-end">
            <button
              type="button"
              onClick={handleGenerateWithAi}
              disabled={isGenerating || isLoadingDeans}
              className="inline-flex min-w-40 items-center justify-center rounded-md bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {isGenerating ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                "Generate with AI"
              )}
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <label
            htmlFor="generated_text"
            className="block text-sm font-medium text-gray-800"
          >
            Application Text
          </label>
          <textarea
            id="generated_text"
            value={generatedText}
            onChange={(event) => setGeneratedText(event.target.value)}
            className="mt-2 min-h-80 block w-full resize-y rounded-md border border-gray-300 bg-white px-4 py-3 text-sm leading-6 text-gray-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
            placeholder="Generated application text will appear here"
          />
        </div>

        {error ? (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-gray-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            {isSubmitting ? "Submitting..." : "Submit Application"}
          </button>
        </div>
      </form>
    </section>
  );
}
