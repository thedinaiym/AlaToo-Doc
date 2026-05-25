"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import type { User } from "@/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const FACULTIES = [
  "Computer Science",
  "Economics",
  "Law",
  "Medicine",
  "Engineering",
];

type CurrentUser = User | null;

export default function BroadcastPage() {
  const router = useRouter();
  const [currentUser] = useState<CurrentUser>(() => {
    if (typeof window === "undefined") {
      return null;
    }

    const storedUser = window.localStorage.getItem("current_user");
    return storedUser ? (JSON.parse(storedUser) as User) : null;
  });
  const [title, setTitle] = useState("");
  const [faculty, setFaculty] = useState(FACULTIES[0]);
  const [text, setText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/admin/broadcast`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title,
          text,
          target_faculty: faculty,
        }),
      });

      if (!response.ok) {
        throw new Error("Broadcast failed.");
      }

      const data = (await response.json()) as { created_count: number };
      setMessage(`Broadcast sent to ${data.created_count} students.`);
      setTitle("");
      setText("");
    } catch {
      setError("Unable to send broadcast.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!currentUser) {
    return (
      <section className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-gray-200 bg-white p-5 text-sm text-gray-600 shadow-sm">
          Loading access...
        </div>
      </section>
    );
  }

  if (currentUser.role !== "admin") {
    return (
      <section className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">
          This page is available only to administrators.
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-950">Mass Distribution</h1>
        <p className="mt-2 text-sm text-gray-600">
          Send one official document to all students in a selected faculty.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
      >
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-800">
              Title
            </label>
            <input
              id="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="mt-2 block w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              placeholder="Announcement title"
              required
            />
          </div>

          <div>
            <label
              htmlFor="faculty"
              className="block text-sm font-medium text-gray-800"
            >
              Faculty
            </label>
            <select
              id="faculty"
              value={faculty}
              onChange={(event) => setFaculty(event.target.value)}
              className="mt-2 block w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
            >
              {FACULTIES.map((facultyName) => (
                <option key={facultyName} value={facultyName}>
                  {facultyName}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-5">
          <label htmlFor="text" className="block text-sm font-medium text-gray-800">
            Message
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(event) => setText(event.target.value)}
            className="mt-2 min-h-56 block w-full resize-y rounded-md border border-gray-300 bg-white px-4 py-3 text-sm leading-6 text-gray-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
            placeholder="Write the document text to distribute"
            required
          />
        </div>

        {message ? (
          <p className="mt-5 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            {message}
          </p>
        ) : null}

        {error ? (
          <p className="mt-5 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <div className="mt-6 flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            {isSubmitting ? "Sending..." : "Send to All Students"}
          </button>
        </div>
      </form>
    </section>
  );
}
